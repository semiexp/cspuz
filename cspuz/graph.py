from cspuz.constraints import count_true, Array
from cspuz.grid_frame import BoolGridFrame


def _check_array_shape(array, dtype, dim):
    return isinstance(array, Array) and array.dtype is dtype and len(array.shape) == dim


class Graph(object):
    def __init__(self, num_vertices):
        self.num_vertices = num_vertices
        self.edges = []
        self.incident_edges = [[] for i in range(self.num_vertices)]

    def __len__(self):
        return len(self.edges)

    def __iter__(self):
        return iter(self.edges)

    def __getitem__(self, item):
        return self.edges[item]

    def add_edge(self, i, j):
        edge_id = len(self.edges)
        self.edges.append((i, j))
        self.incident_edges[i].append((j, edge_id))
        self.incident_edges[j].append((i, edge_id))


def _grid_graph(height, width):
    graph = Graph(height * width)
    for y in range(height):
        for x in range(width):
            if x < width - 1:
                graph.add_edge(y * width + x, y * width + (x + 1))
            if y < height - 1:
                graph.add_edge(y * width + x, (y + 1) * width + x)
    return graph


def _from_grid_frame(grid_frame):
    height = grid_frame.height
    width = grid_frame.width
    edges = []
    graph = Graph((height + 1) * (width + 1))
    for y in range(height + 1):
        for x in range(width + 1):
            if y != height:
                edges.append(grid_frame[y * 2 + 1, x * 2])
                graph.add_edge(y * (width + 1) + x, (y + 1) * (width + 1) + x)
            if x != width:
                edges.append(grid_frame[y * 2, x * 2 + 1])
                graph.add_edge(y * (width + 1) + x, y * (width + 1) + (x + 1))
    return edges, graph


def _active_vertices_connected(solver, is_active, graph):
    n = graph.num_vertices

    ranks = solver.int_array(n, 0, n - 1)
    is_root = solver.bool_array(n)

    for i in range(n):
        less_ranks = [((ranks[j] < ranks[i]) & is_active[j]) for j, _ in graph.incident_edges[i]]
        solver.ensure(is_active[i].then(count_true(less_ranks + [is_root[i]]) >= 1))
    solver.ensure(count_true(is_root) <= 1)


def active_vertices_connected(solver, is_active, graph=None):
    if graph is None:
        if not _check_array_shape(is_active, bool, 2):
            raise TypeError('`is_active` should be a 2-D bool Array if graph is not specified')
        height, width = is_active.shape
        _active_vertices_connected(solver, is_active.flatten(), _grid_graph(height, width))
    else:
        _active_vertices_connected(solver, is_active, graph)


def active_vertices_not_adjacent(solver, is_active, graph=None):
    if graph is None:
        if not _check_array_shape(is_active, bool, 2):
            raise TypeError('`is_active` should be a 2-D bool Array if graph is not specified')
        solver.ensure(~(is_active[1:, :] & is_active[:-1, :]))
        solver.ensure(~(is_active[:, 1:] & is_active[:, :-1]))
    else:
        for i, j in graph:
            solver.ensure(~(is_active[i] & is_active[j]))


def active_vertices_not_adjacent_and_not_segmenting(solver, is_active, graph=None):
    if graph is None:
        if not _check_array_shape(is_active, bool, 2):
            raise TypeError('`is_active` should be a 2-D bool Array if graph is not specified')
        active_vertices_not_adjacent(solver, is_active)
        height, width = is_active.shape
        ranks = solver.int_array((height, width), 0, (height * width - 1) // 2)
        for y in range(height):
            for x in range(width):
                less_ranks = []
                nonzero = False
                for dy in [-1, 1]:
                    for dx in [-1, 1]:
                        y2 = y + dy
                        x2 = x + dx
                        if 0 <= y2 < height and 0 <= x2 < width:
                            less_ranks.append((ranks[y2, x2] < ranks[y, x]) & is_active[y2, x2])
                            if (y2, x2) < (y, x):
                                solver.ensure(ranks[y2, x2] != ranks[y, x])
                        else:
                            nonzero = True
                solver.ensure(is_active[y, x].then(count_true(less_ranks) <= (0 if nonzero else 1)))
    else:
        active_vertices_not_adjacent(solver, is_active, graph)
        active_vertices_connected(solver, ~is_active, graph)  # TODO: is_active may not be an Array


def active_edges_acyclic(solver, is_active_edge, graph):
    n = graph.num_vertices

    ranks = solver.int_array(n, 0, n - 1)

    for i in range(n):
        less_ranks = []
        for j, e in graph.incident_edges[i]:
            less_ranks.append((ranks[j] < ranks[i]) & is_active_edge[e])
            if i < j:
                solver.ensure(ranks[i] != ranks[j])
        solver.ensure(count_true(less_ranks) <= 1)


def _division_connected(solver, division, num_regions, graph, roots=None):
    n = graph.num_vertices
    m = len(graph)

    rank = solver.int_array(n, 0, n - 1)
    is_root = solver.bool_array(n)
    spanning_forest = solver.bool_array(m)

    for i in range(n):
        less_ranks = []
        for j, e in graph.incident_edges[i]:
            less_ranks.append(spanning_forest[e] & (rank[i] > rank[j]))
            if i < j:
                solver.ensure(spanning_forest[e].then((division[i] == division[j]) & (rank[i] != rank[j])))
        solver.ensure(count_true(less_ranks) == is_root[i].cond(0, 1))
    for i in range(num_regions):
        solver.ensure(count_true([r & (n == i) for r, n in zip(is_root, division)]) == 1)
    if roots is not None:
        for i, r in enumerate(roots):
            if r is not None:
                solver.ensure(division[r] == i)
                solver.ensure(is_root[r])


def division_connected(solver, division, num_regions, graph=None, roots=None):
    if graph is None:
        if not _check_array_shape(division, int, 2):
            raise TypeError('`division` should be a 2-D bool Array if graph is not specified')
        height, width = division.shape
        if roots is None:
            roots_conv = None
        else:
            roots_conv = []
            for a in roots:
                if a is None:
                    roots_conv.append(a)
                else:
                    y, x = a
                    roots_conv.append(y * width + x)
        _division_connected(solver, division.flatten(), num_regions, _grid_graph(height, width), roots=roots_conv)
    else:
        _division_connected(solver, division, num_regions, graph, roots=roots)


def _active_edges_single_cycle(solver, is_active_edge, graph):
    n = graph.num_vertices
    m = len(graph)

    rank = solver.int_array(n, 0, n - 1)
    is_passed = solver.bool_array(n)
    is_root = solver.bool_array(n)

    for i in range(n):
        degree = count_true([is_active_edge[e] for j, e in graph.incident_edges[i]])
        solver.ensure(degree == is_passed[i].cond(2, 0))
        solver.ensure(is_passed[i].then(count_true(
            [is_active_edge[e] & (rank[j] >= rank[i]) for j, e in graph.incident_edges[i]]
        ) <= is_root[i].cond(2, 1)))
    solver.ensure(count_true(is_root) == 1)


def active_edges_single_cycle(solver, is_active_edge, graph=None):
    if graph is None:
        if not isinstance(is_active_edge, BoolGridFrame):
            raise TypeError('`is_active_edge` should be a BoolGridFrame if graph is not specified')
        edges, graph = _from_grid_frame(is_active_edge)
        _active_edges_single_cycle(solver, edges, graph)
    else:
        _active_edges_single_cycle(solver, is_active_edge, graph)
