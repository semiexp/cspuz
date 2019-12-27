/*
License

Sugar (A SAT-based CSP Solver) version 2

Copyright (c) 2008-2012
by Naoyuki Tamura (tamura @ kobe-u.ac.jp),
   Tomoya Tanjo, and
   Mutsunori Banbara (banbara @ kobe-u.ac.jp)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

 * Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
 * Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the
   distribution.
 * Neither the name of the Kobe University nor the names of its
   contributors may be used to endorse or promote products derived
   from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

import java.io.*;
import java.util.*;

import jp.kobe_u.sugar.SugarException;
import jp.kobe_u.sugar.expression.Parser;
import jp.kobe_u.sugar.expression.Expression;
import jp.kobe_u.sugar.expression.Sequence;
import jp.kobe_u.sugar.expression.Atom;
import jp.kobe_u.sugar.encoder.Encoder;
import jp.kobe_u.sugar.csp.CSP;
import jp.kobe_u.sugar.converter.Converter;
import jp.kobe_u.sugar.converter.Simplifier;
import jp.kobe_u.sugar.SugarConstants;

class CspuzSugarInterface {
    List<Expression> problem;
    ArrayList<String> intVars, boolVars;
    boolean[] isAnswerKeyInt, isAnswerKeyBool;
    CSP csp;
    String satFile, mapFile, outFile;
    String[] answerKeys;

    void loadProblem() throws IOException {
        ArrayList<String> lines = new ArrayList<String>();
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line;
        answerKeys = null;
        while ((line = reader.readLine()) != null) {
            if (line.startsWith("#")) {
                answerKeys = line.substring(1).split(" ");
            } else {
                lines.add(line);
            }
        }

        String cspDescription = String.join("\n", lines);
        Parser parser = new Parser(new BufferedReader(new StringReader(cspDescription)));
        problem = parser.parse();

        intVars = new ArrayList<String>();
        boolVars = new ArrayList<String>();

        for (Expression e : problem) {
            Sequence seq = (Sequence)e;
            if (((Atom)seq.get(0)).stringValue().equals(SugarConstants.INT_DEFINITION)) {
                String name = ((Atom)seq.get(1)).stringValue();
                intVars.add(name);
            } else if (((Atom)seq.get(0)).stringValue().equals(SugarConstants.BOOL_DEFINITION)) {
                String name = ((Atom)seq.get(1)).stringValue();
                boolVars.add(name);
            }
        }

        if (answerKeys != null) {
            HashSet<String> answerKeySet = new HashSet<String>();
            for (int i = 0; i < answerKeys.length; ++i) {
                answerKeySet.add(answerKeys[i]);
            }
            isAnswerKeyInt = new boolean[intVars.size()];
            for (int i = 0; i < intVars.size(); ++i) {
                isAnswerKeyInt[i] = answerKeySet.contains(intVars.get(i));
            }
            isAnswerKeyBool = new boolean[boolVars.size()];
            for (int i = 0; i < boolVars.size(); ++i) {
                isAnswerKeyBool[i] = answerKeySet.contains(boolVars.get(i));
            }
        }
    }
    private File tempFile(String name, String ext) throws IOException {
        File file = File.createTempFile(name, ext);
        file.deleteOnExit();
        return file;
    }
    private void setupTempFiles() throws IOException {
        satFile = tempFile("temp", ".cnf").getAbsolutePath();
        mapFile = tempFile("temp", ".map").getAbsolutePath();
        outFile = tempFile("temp", ".out").getAbsolutePath();
    }
    boolean solveCSP() throws IOException, SugarException {
        // CSP -> SAT
        csp = new CSP();
        Converter converter = new Converter(csp);
        converter.convert(problem);
        csp.propagate();
        if (csp.isUnsatisfiable()) {
            return false;
        }
        Simplifier simplifier = new Simplifier(csp);
        simplifier.simplify();
        if (csp.isUnsatisfiable()) {
            return false;
        }
        Encoder encoder = new Encoder(csp);
        encoder.encode(satFile);
        encoder.outputMap(mapFile);

        // Solve SAT
        String command[] = new String[] { "minisat", satFile, outFile };
        Process process = Runtime.getRuntime().exec(command);
        try {
            process.waitFor();
        } catch (InterruptedException e) {
	        process.destroy();
	        e.printStackTrace();
        }
        
        return encoder.decode(outFile);
    }
    void run() throws IOException, SugarException {
        loadProblem();
        setupTempFiles();
        boolean isSat = solveCSP();

        if (answerKeys == null) {
            // answer finder mode
            if (isSat) {
                System.out.println("s SATISFIABLE");
                for (String name : intVars) {
                    System.out.println("a " + name + "\t" + csp.getIntegerVariable(name).getValue());
                }
                for (String name : boolVars) {
                    System.out.println("a " + name + "\t" + csp.getBooleanVariable(name).getValue());
                }
                System.out.println("a");
            } else {
                System.out.println("s UNSATISFIABLE");
            }
        } else {
            // deduction mode
            if (!isSat) {
                System.out.println("unsat");
                return;
            }
            boolean[] notRefutedInt = new boolean[isAnswerKeyInt.length];
            boolean[] notRefutedBool = new boolean[isAnswerKeyBool.length];
            int[] answerInt = new int[isAnswerKeyInt.length];
            boolean[] answerBool = new boolean[isAnswerKeyBool.length];
            for (int i = 0; i < isAnswerKeyInt.length; ++i) {
                notRefutedInt[i] = isAnswerKeyInt[i];
                answerInt[i] = csp.getIntegerVariable(intVars.get(i)).getValue();
            }
            for (int i = 0; i < isAnswerKeyBool.length; ++i) {
                notRefutedBool[i] = isAnswerKeyBool[i];
                answerBool[i] = csp.getBooleanVariable(boolVars.get(i)).getValue();
            }
            while (true) {
                List<Expression> refutingExpr = new ArrayList<Expression>();
                for (int i = 0; i < isAnswerKeyInt.length; ++i) {
                    if (notRefutedInt[i]) {
                        refutingExpr.add(Expression.create(intVars.get(i)).ne(answerInt[i]));
                    }
                }
                for (int i = 0; i < isAnswerKeyBool.length; ++i) {
                    if (notRefutedBool[i]) {
                        refutingExpr.add(Expression.create(boolVars.get(i)).xor(Expression.create(String.valueOf(answerBool[i]))));
                    }
                }
                problem.add(Expression.create(Expression.OR, refutingExpr));

                isSat = solveCSP();
                if (!isSat) {
                    break;
                }
                for (int i = 0; i < isAnswerKeyInt.length; ++i) {
                    if (answerInt[i] != csp.getIntegerVariable(intVars.get(i)).getValue()) {
                        notRefutedInt[i] = false;
                    }
                }
                for (int i = 0; i < isAnswerKeyBool.length; ++i) {
                    if (answerBool[i] != csp.getBooleanVariable(boolVars.get(i)).getValue()) {
                        notRefutedBool[i] = false;
                    }
                }
            }
            System.out.println("sat");
            for (int i = 0; i < isAnswerKeyInt.length; ++i) {
                if (isAnswerKeyInt[i] && notRefutedInt[i]) {
                    System.out.println(intVars.get(i) + " " + answerInt[i]);
                }
            }
            for (int i = 0; i < isAnswerKeyBool.length; ++i) {
                if (isAnswerKeyBool[i] && notRefutedBool[i]) {
                    System.out.println(boolVars.get(i) + " " + answerBool[i]);
                }
            }
        }
    }
    public static void main(String[] args) throws IOException, SugarException {
        CspuzSugarInterface inf = new CspuzSugarInterface();
        inf.run();
    }
}
