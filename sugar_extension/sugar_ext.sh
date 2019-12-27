#!/bin/bash
cd `dirname $0`
java -cp ".:${SUGAR_JAR}" CspuzSugarInterface
