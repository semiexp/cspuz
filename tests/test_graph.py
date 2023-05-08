import pytest

import cspuz
from cspuz import graph, BoolGridFrame


class TestGraph:
    @pytest.fixture(
        autouse=True,
        params=[
            ("sugar", False, False),
            ("sugar", True, False),
            ("z3", False, False),
            ("enigma_csp", True, True),
        ],
    )
    def default_backend(self, request):
        default_backend, use_graph_primitive, use_graph_division_primitive = request.param
        cspuz.config.default_backend = default_backend
        cspuz.config.use_graph_primitive = use_graph_primitive
        cspuz.config.use_graph_division_primitive = use_graph_division_primitive

    @pytest.fixture
    def solver(self):
        return cspuz.Solver()

    @pytest.fixture
    def default_graph(self):
        # 0 - 1 - 2
        # |   |   |
        # 3 - 4 - 5
        # |   |
        # 6 - 7
        g = graph.Graph(8)
        g.add_edge(0, 1)
        g.add_edge(0, 3)
        g.add_edge(1, 2)
        g.add_edge(1, 4)
        g.add_edge(2, 5)
        g.add_edge(3, 4)
        g.add_edge(3, 6)
        g.add_edge(4, 5)
        g.add_edge(4, 7)
        g.add_edge(6, 7)
        return g

    def test_graph_len(self, default_graph):
        assert len(default_graph) == 10

    def test_graph_getitem(self, default_graph):
        assert default_graph[4] == (2, 5)

    def test_active_vertices_connected_grid(self, solver):
        is_active = solver.bool_array((3, 4))
        graph.active_vertices_connected(solver, is_active)

        solver.ensure(~is_active[0, 0])
        solver.ensure(~is_active[1, 1])
        solver.ensure(~is_active[1, 2])
        solver.ensure(is_active[0, 1])
        solver.ensure(is_active[1, 0])
        assert solver.find_answer()

        solver.ensure(~is_active[2, 3])
        assert not solver.find_answer()

    def test_active_vertices_connected_graph(self, solver, default_graph):
        is_active = solver.bool_array(8)
        graph.active_vertices_connected(solver, is_active, graph=default_graph)

        solver.ensure(~is_active[0])
        solver.ensure(~is_active[4])
        solver.ensure(is_active[5])
        assert solver.find_answer()

        solver.ensure(is_active[7])
        assert not solver.find_answer()

    def test_active_vertices_not_adjacent_and_not_segmenting_grid(self, solver):
        is_active = solver.bool_array((3, 4))
        solver.add_answer_key(is_active)
        graph.active_vertices_not_adjacent_and_not_segmenting(solver, is_active)

        solver.ensure(is_active[1, 1])
        solver.ensure(is_active[2, 2])
        assert solver.solve()
        assert is_active[0, 0].sol is False
        assert is_active[0, 2].sol is False
        assert is_active[0, 3].sol is None

    def test_active_vertices_not_adjacent_and_not_segmenting_graph(self, solver, default_graph):
        is_active = solver.bool_array(8)
        solver.add_answer_key(is_active)
        graph.active_vertices_not_adjacent_and_not_segmenting(
            solver, is_active, graph=default_graph
        )

        solver.ensure(is_active[0])
        assert solver.find_answer()
        assert is_active[4].sol is False

    def test_active_edges_acyclic(self, solver, default_graph):
        is_active_edge = solver.bool_array(10)
        graph.active_edges_acyclic(solver, is_active_edge, default_graph)

        solver.ensure(is_active_edge[3])
        solver.ensure(is_active_edge[7])
        solver.ensure(is_active_edge[4])
        assert solver.find_answer()

        solver.ensure(is_active_edge[2])
        assert not solver.find_answer()

    def test_division_connected_grid(self, solver):
        division = solver.int_array((5, 5), 0, 3)
        solver.add_answer_key(division)
        graph.division_connected(solver, division, 4)

        solver.ensure(division[1, 2] == 1)
        solver.ensure(division[1, 3] == 3)
        solver.ensure(division[2, 1] == 2)
        solver.ensure(division[2, 4] == 0)
        solver.ensure(division[4, 1] == 0)
        solver.ensure(division[4, 2] == 1)
        assert solver.solve()
        assert division[0, 1].sol == 0
        assert division[0, 2].sol == 0
        assert division[0, 3].sol == 0
        assert division[2, 2].sol == 1
        assert division[1, 0].sol == 0
        assert division[2, 0].sol == 0
        assert division[3, 0].sol == 0

    def test_division_connected_grid_roots(self, solver):
        division = solver.int_array((5, 5), 0, 3)
        solver.add_answer_key(division)
        graph.division_connected(solver, division, 4, roots=[(2, 4), (1, 2), None, None])

        solver.ensure(division[1, 3] == 3)
        solver.ensure(division[2, 1] == 2)
        solver.ensure(division[4, 1] == 0)
        solver.ensure(division[4, 2] == 1)
        assert solver.solve()
        assert division[0, 1].sol == 0
        assert division[0, 2].sol == 0
        assert division[0, 3].sol == 0
        assert division[2, 2].sol == 1
        assert division[1, 0].sol == 0
        assert division[2, 0].sol == 0
        assert division[3, 0].sol == 0

    def test_division_connected_graph(self, solver, default_graph):
        division = solver.int_array(8, 0, 1)
        solver.add_answer_key(division)
        graph.division_connected(solver, division, 2, graph=default_graph)

        solver.ensure(division[1] == 1)
        solver.ensure(division[2] == 0)
        solver.ensure(division[7] == 1)
        assert solver.solve()
        assert division[0].sol == 1
        assert division[3].sol == 1
        assert division[6].sol == 1

    def test_division_connected_graph_roots(self, solver, default_graph):
        division = solver.int_array(8, 0, 1)
        solver.add_answer_key(division)
        graph.division_connected(solver, division, 2, graph=default_graph, roots=[None, 7])

        solver.ensure(division[1] == 1)
        solver.ensure(division[2] == 0)
        assert solver.solve()
        assert division[0].sol == 1
        assert division[3].sol == 1
        assert division[6].sol == 1

    def test_division_connected_variable_groups_grid(self, solver):
        group_id = graph.division_connected_variable_groups(
            solver,
            shape=(4, 4),
            group_size=[
                [6, None, None, None],
                [None, None, None, None],
                [None, None, 5, None],
                [None, None, 6, None],
            ],
        )
        solver.add_answer_key(group_id)
        assert solver.find_answer()

    def test_active_edges_single_cycle_grid_frame(self, solver):
        grid_frame = BoolGridFrame(solver, 4, 4)
        solver.add_answer_key(grid_frame)
        graph.active_edges_single_cycle(solver, grid_frame)

        solver.ensure(~grid_frame.vertical[1, 0])
        solver.ensure(grid_frame.vertical[1, 1])
        solver.ensure(~grid_frame.vertical[1, 3])
        solver.ensure(~grid_frame.vertical[1, 4])
        solver.ensure(~grid_frame.horizontal[3, 1])
        solver.ensure(grid_frame.vertical[3, 3])
        assert solver.solve()
        assert grid_frame.vertical[1, 2].sol is True
        assert grid_frame.horizontal[4, 1].sol is True
        assert grid_frame.horizontal[2, 1].sol is False
        assert grid_frame.horizontal[1, 1].sol is None
        assert grid_frame.horizontal[2, 2].sol is None
        assert grid_frame.horizontal[2, 3].sol is None

    def test_active_edges_single_cycle_graph(self, solver, default_graph):
        is_active_edge = solver.bool_array(10)
        solver.add_answer_key(is_active_edge)
        graph.active_edges_single_cycle(solver, is_active_edge, graph=default_graph)

        solver.ensure(is_active_edge[0])
        solver.ensure(~is_active_edge[5])
        assert solver.solve()
        assert is_active_edge[4].sol is None
        assert is_active_edge[9].sol is True

    def test_division_connected_variable_groups_with_borders(self, solver, default_graph):
        v = solver.int_var(1, 8)
        is_border = solver.bool_array(10)
        solver.add_answer_key(is_border)
        graph.division_connected_variable_groups_with_borders(
            solver, graph=default_graph, group_size=[v] * 8, is_border=is_border
        )

        # TODO: with these constraints the solver does not terminate
        solver.ensure(~is_border[1])
        solver.ensure(is_border[9])

        assert solver.solve()
        assert is_border[4].sol is False
        assert is_border[5].sol is True
