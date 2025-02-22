"""A module for graph-related constraints.

This module provides constraints related to graphs, such as connectivity and division of vertices
into connected components.

.. _auto_inference_of_graph:

Auto-inference of graph
=======================

For some constraints, the graph is automatically inferred from the input.

2D array (:py:class:`BoolArray2D`, :py:class:`IntArray2D`)
    For 2D arrays, the grid graph is automatically inferred from the array. Suppose the shape of
    the array is (height, width). Cell (i, j) (0 <= i < height, 0 <= j < width) corresponds to
    vertex i * width + j in the grid graph. The edges are added between horizontally and vertically
    adjacent cells. That is, vertices adjacent to i * width + j are as follows:

    - i * width + (j + 1) (if j < width - 1)
    - i * width + (j - 1) (if j > 0)
    - (i + 1) * width + j (if i < height - 1)
    - (i - 1) * width + j (if i > 0)

2D grid frame (:py:class:`BoolGridFrame`)
    For 2D grid frames, the grid graph is automatically inferred from the frame. Suppose the grid
    frame represents edges of a height * width grid. Then the inferred graph has
    (height + 1) * (width + 1) vertices corresponding to the intersections of horizontal and
    vertical edges. The edges are added between horizontally and vertically adjacent intersections.

    (TODO: add formal definition)
"""

from typing import Any, Iterator, List, Optional, Sequence, Tuple, Union, cast, overload

from .array import Array2D, BoolArray1D, BoolArray2D, IntArray1D, IntArray2D, _infer_shape
from .constraints import IntExpr, BoolExpr, Op, count_true, then
from .expr import BoolExprLike, IntExprLike
from .grid_frame import BoolGridFrame, BoolInnerGridFrame
from .configuration import config
from .solver import Solver


class Graph(object):
    """Class for a undirected graph."""

    #: The number of vertices in the graph.
    num_vertices: int

    #: List of edges represented by pairs of vertex indices.
    edges: List[Tuple[int, int]]

    #: List of incident edges for each vertex.
    #:
    #: Each element is a list of pairs of vertex. indices and edge indices.
    incident_edges: List[List[Tuple[int, int]]]

    def __init__(self, num_vertices: int) -> None:
        self.num_vertices = num_vertices
        self.edges = []
        self.incident_edges = [[] for i in range(self.num_vertices)]

    def __len__(self) -> int:
        return len(self.edges)

    def __iter__(self) -> Iterator[Tuple[int, int]]:
        return iter(self.edges)

    def __getitem__(self, item: int) -> Tuple[int, int]:
        return self.edges[item]

    def add_edge(self, i: int, j: int) -> None:
        """Add an edge connecting vertices `i` and `j`.

        Args:
            i (int): the index of the first vertex
            j (int): the index of the second vertex
        """
        edge_id = len(self.edges)
        self.edges.append((i, j))
        self.incident_edges[i].append((j, edge_id))
        self.incident_edges[j].append((i, edge_id))

    def line_graph(self) -> "Graph":
        """Return the "line graph" of this graph.

        The line graph of a graph is a graph whose vertices correspond to the edges of
        the original graph, and two vertices are connected by an edge if the corresponding edges
        share a vertex in the original graph.

        In the returned graph, the vertices (corresponding to the edges of the original graph) are
        numbered from 0 to (the number of edges) - 1 in the same order as the original graph.
        On the other hand, the order of edges in the returned graph is not guaranteed.

        Example:
            >>> g = Graph(4)
            >>> g.add_edge(0, 1)
            >>> g.add_edge(1, 2)
            >>> g.add_edge(0, 2)
            >>> g.add_edge(2, 3)
            >>> lg = g.line_graph()
            >>> len(lg)
            5
        """
        n = self.num_vertices
        edges = set()
        for v in range(n):
            for i in range(len(self.incident_edges[v])):
                for j in range(i):
                    x = self.incident_edges[v][i][1]
                    y = self.incident_edges[v][j][1]
                    if x < y:
                        edges.add((x, y))
                    else:
                        edges.add((y, x))
        ret = Graph(len(self))
        for x, y in edges:
            ret.add_edge(x, y)
        return ret


def _get_array_shape_2d(array: Array2D | Sequence[Sequence[Any]]) -> tuple[int, int]:
    if isinstance(array, Array2D):
        return array.shape
    else:
        shape = _infer_shape(array)
        return shape


def _grid_graph(height: int, width: int) -> Graph:
    graph = Graph(height * width)
    for y in range(height):
        for x in range(width):
            if x < width - 1:
                graph.add_edge(y * width + x, y * width + (x + 1))
            if y < height - 1:
                graph.add_edge(y * width + x, (y + 1) * width + x)
    return graph


def _from_grid_frame(grid_frame: BoolGridFrame) -> tuple[Sequence[BoolExprLike], Graph]:
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


def _active_vertices_connected(
    solver: Solver,
    is_active: Sequence[BoolExprLike],
    graph: Graph,
    acyclic: bool = False,
    use_graph_primitive: Optional[bool] = None,
) -> None:
    if use_graph_primitive is None:
        use_graph_primitive = config.use_graph_primitive
    if use_graph_primitive and not acyclic:
        if len(is_active) != graph.num_vertices:
            raise ValueError(
                "is_active must have the same number of items as that of vertices in graph"
            )
        solver.ensure(
            BoolExpr(
                Op.GRAPH_ACTIVE_VERTICES_CONNECTED,
                [graph.num_vertices, len(graph)]
                + [is_active[i] for i in range(len(is_active))]  # type: ignore
                + sum([[x, y] for x, y in graph.edges], []),  # type: ignore
            )
        )
        return

    n = graph.num_vertices

    ranks = solver.int_array(n, 0, n - 1)
    is_root = solver.bool_array(n)

    for i in range(n):
        less_ranks = [((ranks[j] < ranks[i]) & is_active[j]) for j, _ in graph.incident_edges[i]]
        if acyclic:
            for j, _ in graph.incident_edges[i]:
                if i < j:
                    solver.ensure(ranks[j] != ranks[i])
            solver.ensure(then(is_active[i], count_true(less_ranks + [is_root[i]]) == 1))
        else:
            solver.ensure(then(is_active[i], count_true(less_ranks + [is_root[i]]) >= 1))
    solver.ensure(count_true(is_root) <= 1)


@overload
def active_vertices_connected(
    solver: Solver,
    is_active: Union[Sequence[BoolExprLike], BoolArray1D],
    graph: Graph,
    *,
    acyclic: bool = False,
    use_graph_primitive: Optional[bool] = None,
) -> None: ...


@overload
def active_vertices_connected(
    solver: Solver,
    is_active: BoolArray2D,
    *,
    acyclic: bool = False,
    use_graph_primitive: Optional[bool] = None,
) -> None: ...


def active_vertices_connected(
    solver: Solver,
    is_active: Union[Sequence[BoolExprLike], BoolArray1D, BoolArray2D],
    graph: Optional[Graph] = None,
    *,
    acyclic: bool = False,
    use_graph_primitive: Optional[bool] = None,
) -> None:
    """Add a constraint that all "active" vertices are "connected" in the given `graph`.

    `is_active` must have the same number of elements as the number of vertices in `graph` (or
    `graph` must be able to be inferred from `is_active`; described later). Then, "active" vertices
    are those whose corresponding boolean value in `is_active` is true. All active vertices are
    "connected" if, for any active vertices u and v, v is reachable from u via a path in the graph
    consisting only of active vertices, or more formally, the induced subgraph by all active
    vertices are connected.

    We note that, if all vertices are inactive (i.e., all elements in `is_active` are false), this
    constaint is satisfied.

    If `is_active` is :class:`BoolArray2D`, the graph is automatically inferred from it
    (:ref:`auto_inference_of_graph`). In this case, the constraint states that all active cells
    are connected.

    Args:
        solver (~cspuz.solver.Solver):
            The :py:class:`~cspuz.solver.Solver` object to which this constraint should be added.
        is_active (Union[Sequence[BoolExprLike], BoolArray1D, BoolArray2D]):
            Sequence of boolean values or :class:`BoolArray2D` representing whether
            vertices are active or not.
        graph (Optional[Graph], optional):
            Graph for this constraint. If `is_active` is :class:`BoolArray2D`, this is
            automatically inferred and should be omitted.
        acyclic (bool, optional):
            If `True` is specified, not only active vertices are expected to be connected, they
            should be "acyclic": there must be a unique path (consisting only of active vetcies)
            between any pair of two active vertices. Note that if this option is enabled,
            primitive graph operators are not used even if `use_graph_primitive` is `True`.
        use_graph_primitive (Optional[bool], optional):
            Whether primitive graph operators are used to represent this constraint. If omitted,
            the default configuration is used. Such operators are available in `sugar`,
            `sugar_extended`, `csugar` and `enigma_csp` backends, but depending on
            the configuration of the backend executable, they may not be supported.

    Raises:
        TypeError: If `graph` is not inferred from `is_active` and unspecified, or inferred and
            explicitly specified.
    """
    if graph is None:
        if not isinstance(is_active, BoolArray2D):
            raise TypeError("'is_active' should be a BoolArray2D if graph is not " "specified")
        height, width = is_active.shape
        is_active2: Sequence[BoolExprLike] = is_active.flatten().data
        graph2 = _grid_graph(height, width)
    else:
        if isinstance(is_active, BoolArray2D):
            raise TypeError("'is_active' should be sequence-like if graph is specified")
        elif isinstance(is_active, BoolArray1D):
            is_active2 = is_active.data
        else:
            is_active2 = is_active
        graph2 = graph

    _active_vertices_connected(
        solver, is_active2, graph2, acyclic=acyclic, use_graph_primitive=use_graph_primitive
    )


@overload
def active_vertices_not_adjacent(
    solver: Solver, is_active: Union[Sequence[BoolExprLike], BoolArray1D], graph: Graph
) -> None: ...


@overload
def active_vertices_not_adjacent(solver: Solver, is_active: BoolArray2D) -> None: ...


def active_vertices_not_adjacent(
    solver: Solver,
    is_active: Union[Sequence[BoolExprLike], BoolArray1D, BoolArray2D],
    graph: Optional[Graph] = None,
) -> None:
    """Add a constraint that no two "active" vertices are adjacent in the given `graph`.

    For each edge (u, v) in the graph, this constraint ensures that both u and v are not active,
    that is, at least one of `is_active[u]` and `is_active[v]` is false.

    If `is_active` is :class:`BoolArray2D`, the graph is automatically inferred from it
    (:ref:`auto_inference_of_graph`). In this case, the constraint states that active cells are
    not adjacent.

    Args:
        solver (~cspuz.solver.Solver):
            The :py:class:`~cspuz.solver.Solver` object to which this constraint should be added.
        is_active (Union[Sequence[BoolExprLike], BoolArray1D, BoolArray2D]):
            Sequence of boolean values or :class:`BoolArray2D` representing whether
            vertices are active or not.
        graph (Optional[Graph], optional):
            Graph for this constraint. If `is_active` is :class:`BoolArray2D`, this is
            automatically inferred and should be omitted.
    """
    if graph is None:
        if not isinstance(is_active, BoolArray2D):
            raise TypeError("'is_active' should be a BoolArray2D if graph is not " "specified")
        solver.ensure(~(is_active[1:, :] & is_active[:-1, :]))
        solver.ensure(~(is_active[:, 1:] & is_active[:, :-1]))
    else:
        if isinstance(is_active, BoolArray2D):
            raise TypeError("'is_active' should be sequence-like if graph is specified")
        for i, j in graph:
            solver.ensure(~(is_active[i] & is_active[j]))


@overload
def active_vertices_not_adjacent_and_not_segmenting(
    solver: Solver, is_active: BoolArray1D, graph: Graph
) -> None: ...


@overload
def active_vertices_not_adjacent_and_not_segmenting(
    solver: Solver, is_active: BoolArray2D
) -> None: ...


# TODO: support Sequence[BoolExprLike]
def active_vertices_not_adjacent_and_not_segmenting(
    solver: Solver, is_active: Union[BoolArray1D, BoolArray2D], graph: Optional[Graph] = None
) -> None:
    """Add a constraint that no two "active" vertices are adjacent and the active vertices do not
    segment the graph into multiple connected components.

    Constraints added by this function are equivalent to the conjunction of those added by calling
    :func:`active_vertices_not_adjacent` (same `is_active`) and :func:`active_vertices_connected`
    (negated `is_active`). However, for :py:class:`BoolArray2D`, this function encodes the
    constraints in a different way. For backend which does not support primitive graph operators
    (e.g. z3), this function may be more efficient than calling the two functions separately.
    However, for backends supporting primitive graph operators (e.g. cspuz_core), this function
    may be less efficient.

    TODO: switch encoding based on `use_graph_primitive`

    Args:
        solver (~cspuz.solver.Solver):
            The :py:class:`~cspuz.solver.Solver` object to which this constraint should be added.
        is_active (Union[Sequence[BoolExprLike], BoolArray1D, BoolArray2D]):
            Sequence of boolean values or :py:class:`BoolArray2D` representing whether
            vertices are active or not.
        graph (Optional[Graph], optional):
            Graph for this constraint. If `is_active` is :py:class:`BoolArray2D`, this is
            automatically inferred and should be omitted.
    """
    if graph is None:
        if not isinstance(is_active, BoolArray2D):
            raise TypeError("'is_active' should be a BoolArray2D if graph is not " "specified")
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
                solver.ensure(
                    is_active[y, x].then(count_true(less_ranks) <= (0 if nonzero else 1))
                )
    else:
        if isinstance(is_active, BoolArray2D):
            raise TypeError("'is_active' should be sequence-like if graph is specified")
        active_vertices_not_adjacent(solver, is_active, graph)
        active_vertices_connected(solver, ~is_active, graph)


def active_edges_acyclic(
    solver: Solver, is_active_edge: Union[Sequence[BoolExprLike], BoolArray1D], graph: Graph
) -> None:
    """Add a constraint that active edges form an acyclic graph (forest).

    This constraint ensures that the subgraph induced by active edges does not contain any cycle.
    That is, the subgraph is a forest.

    Args:
        solver (~cspuz.solver.Solver):
            The :py:class:`~cspuz.solver.Solver` object to which this constraint should be added.
        is_active_edge (Union[Sequence[BoolExprLike], BoolArray1D]):
            Sequence of boolean values representing whether edges are active or not.
        graph (Graph):
            The graph on which this constraint is applied.
    """
    n = graph.num_vertices

    ranks = solver.int_array(n, 0, n - 1)

    for i in range(n):
        less_ranks = []
        for j, e in graph.incident_edges[i]:
            less_ranks.append((ranks[j] < ranks[i]) & is_active_edge[e])
            if i < j:
                solver.ensure(ranks[i] != ranks[j])
        solver.ensure(count_true(less_ranks) <= 1)


def _division_connected(
    solver: Solver,
    division: Union[Sequence[IntExprLike], IntArray1D],
    num_regions: int,
    graph: Graph,
    roots: Optional[Sequence[Optional[int]]] = None,
    allow_empty_group: bool = False,
    use_graph_primitive: Optional[bool] = None,
) -> None:
    if use_graph_primitive is None:
        use_graph_primitive = config.use_graph_primitive

    n = graph.num_vertices
    m = len(graph)

    if use_graph_primitive:
        for i in range(num_regions):
            region = solver.bool_array(n)
            solver.ensure(region == (division == i))
            _active_vertices_connected(solver, region.data, graph, use_graph_primitive=True)

            if not allow_empty_group:
                solver.ensure(count_true(region) >= 1)

        if roots is not None:
            for i, r in enumerate(roots):
                if r is not None:
                    if not isinstance(r, int):
                        raise TypeError("each element in 'roots' must be 'int'")
                    solver.ensure(division[r] == i)
        return

    rank = solver.int_array(n, 0, n - 1)
    is_root = solver.bool_array(n)
    spanning_forest = solver.bool_array(m)

    for i in range(n):
        less_ranks = []
        for j, e in graph.incident_edges[i]:
            less_ranks.append(spanning_forest[e] & (rank[i] > rank[j]))
            if i < j:
                solver.ensure(
                    spanning_forest[e].then((division[i] == division[j]) & (rank[i] != rank[j]))
                )
        solver.ensure(count_true(less_ranks) == is_root[i].cond(0, 1))
    for i in range(num_regions):
        if allow_empty_group:
            solver.ensure(count_true([r & (n == i) for r, n in zip(is_root, division)]) <= 1)
        else:
            solver.ensure(count_true([r & (n == i) for r, n in zip(is_root, division)]) == 1)
    if roots is not None:
        for i, r in enumerate(roots):
            if r is not None:
                solver.ensure(division[r] == i)
                solver.ensure(is_root[r])


@overload
def division_connected(
    solver: Solver,
    division: Union[Sequence[IntExprLike], IntArray1D],
    num_regions: int,
    graph: Graph,
    *,
    roots: Optional[Sequence[Optional[int]]] = None,
    allow_empty_group: bool = False,
) -> None: ...


@overload
def division_connected(
    solver: Solver,
    division: IntArray2D,
    num_regions: int,
    *,
    roots: Optional[Sequence[Optional[int]]] = None,
    allow_empty_group: bool = False,
) -> None: ...


def division_connected(
    solver: Solver,
    division: Union[Sequence[IntExprLike], IntArray1D, IntArray2D],
    num_regions: int,
    graph: Optional[Graph] = None,
    *,
    roots: Union[Sequence[Optional[int]], Sequence[Optional[Tuple[int, int]]], None] = None,
    allow_empty_group: bool = False,
) -> None:
    """Add a constraint that vertices are divided into connected components represented by
    `division`.

    The constraint ensures that the vertices are divided into `num_regions` connected components.
    Each connected component is numbered from 0 to `num_regions - 1`. `division` is a sequence of
    numbers representing the connected component to which each vertex belongs.

    If `division` is a :class:`IntArray2D`, the graph is automatically inferred from it
    (:ref:`auto_inference_of_graph`).

    Performance consideration
        (TODO)

    Args:
        solver (~cspuz.solver.Solver):
            The :py:class:`~cspuz.solver.Solver` object to which this constraint should be added.
        division (Union[Sequence[IntExprLike], IntArray1D, IntArray2D]):
            Sequence of integer values or :py:class:`IntArray2D` representing the connected
            components to which vertices belong.
        num_regions (int):
            The number of connected components.
        graph (Optional[Graph], optional):
            Graph for this constraint. If `division` is :py:class:`IntArray2D`, this is
            automatically inferred and should be omitted.
        roots (Union[Sequence[Optional[int]], Sequence[Optional[Tuple[int, int]]], None], optional):
            If specified, it should be a sequence of vertices that must belong to the corresponding
            connected component. Each element should be either an integer representing the vertex
            index or a tuple of two integers representing the coordinates of the vertex in the
            grid (if `division` is :py:class:`IntArray2D`).
        allow_empty_group (bool, optional):
            If `True` is specified, empty connected components are allowed. Otherwise, all
            connected components must have at least one vertex. (default: `False`)
    """  # noqa: E501
    if graph is None:
        if not isinstance(division, IntArray2D):
            raise TypeError("'division' should be a IntArray2D if graph is not " "specified")
        height, width = division.shape
        if roots is None:
            roots_conv: Optional[List[Optional[int]]] = None
        else:
            roots_conv = []
            for a in roots:
                if a is None:
                    roots_conv.append(a)
                else:
                    if isinstance(a, int):
                        raise TypeError(
                            "each element in 'roots' must be tuple (y, x) "
                            "if 'division' is an IntArray2D"
                        )
                    y, x = a
                    roots_conv.append(y * width + x)
        _division_connected(
            solver,
            division.flatten(),
            num_regions,
            _grid_graph(height, width),
            roots=roots_conv,
            allow_empty_group=allow_empty_group,
        )
    else:
        if isinstance(division, IntArray2D):
            raise TypeError("'division' should be sequence-like if graph is specified")
        _division_connected(
            solver,
            division,
            num_regions,
            graph,
            roots=cast("Sequence[Optional[int]]", roots),
            allow_empty_group=allow_empty_group,
        )


def _division_connected_variable_groups(
    solver: Solver,
    graph: Graph,
    group_size: Union[None, IntArray1D, IntExprLike, Sequence[Optional[IntExprLike]]] = None,
) -> IntArray1D:
    n = graph.num_vertices
    m = len(graph)

    group_id = solver.int_array(n, 0, n - 1)
    rank = solver.int_array(n, 0, n - 1)
    is_root = solver.bool_array(n)
    is_active_edge = solver.bool_array(m)
    solver.ensure(is_root == (rank == 0))

    for i in range(n):
        solver.ensure(is_root[i].then(group_id[i] == i))
        for j, e in graph.incident_edges[i]:
            solver.ensure(is_active_edge[e].then(rank[j] != rank[i]))
        solver.ensure(
            count_true(
                [is_active_edge[e] & (rank[j] < rank[i]) for j, e in graph.incident_edges[i]]
            )
            == is_root[i].cond(0, 1)
        )
    for i, (u, v) in enumerate(graph):
        solver.ensure(is_active_edge[i].then(group_id[u] == group_id[v]))
    if group_size is not None:
        downstream_size = solver.int_array(n, 1, n)
        total_size = solver.int_array(n, 1, n)
        solver.ensure(downstream_size <= total_size)
        solver.ensure(is_root.then(downstream_size == total_size))
        for i in range(n):
            solver.ensure(
                sum(
                    [
                        (is_active_edge[e] & (rank[j] > rank[i])).cond(downstream_size[j], 0)
                        for j, e in graph.incident_edges[i]
                    ]
                )
                + 1
                == downstream_size[i]
            )

            if isinstance(group_size, (int, IntExpr)):
                s: Optional[IntExprLike] = group_size
            else:
                gi = group_size[i]
                if gi is not None and not isinstance(gi, (int, IntExpr)):
                    raise TypeError("invalid type for element of 'group_size'")
                s = gi
            if s is not None:
                solver.ensure(total_size[i] == s)
        if not isinstance(group_size, (int, IntExpr)):
            for i, (u, v) in enumerate(graph):
                s = total_size[u]
                t = total_size[v]
                solver.ensure(is_active_edge[i].then(s == t))
    return group_id


@overload
def division_connected_variable_groups(
    solver: Solver,
    *,
    shape: Optional[Tuple[int, int]] = None,
    group_size: Union[
        None, IntExprLike, IntArray2D, Sequence[Sequence[Optional[IntExprLike]]]
    ] = None,
) -> IntArray2D: ...


@overload
def division_connected_variable_groups(
    solver: Solver,
    *,
    graph: Graph,
    group_size: Union[None, IntExprLike, IntArray1D, Sequence[Optional[IntExprLike]]] = None,
) -> IntArray1D: ...


def division_connected_variable_groups(
    solver: Solver,
    *,
    graph: Optional[Graph] = None,
    shape: Optional[Tuple[int, int]] = None,
    group_size: Union[
        None,
        IntExprLike,
        IntArray1D,
        Sequence[Optional[IntExprLike]],
        IntArray2D,
        Sequence[Sequence[Optional[IntExprLike]]],
    ] = None,
) -> IntArray1D | IntArray2D:
    """Add a constraint that partitions the vertices of a graph into connected components, where
    each component has a size specified by `group_size`.

    If `graph` is specified, the constraint is applied to that graph. Otherwise, `shape` should be
    given, and the constraint is applied to the grid graph of the specified shape.

    This function returns a sequence or a 2D array of integer variables, where each variable
    represents the connected component to which the corresponding vertex belongs. Two vertices
    have the same value if and only if they are in the same connected component. The size of each
    connected component must match the corresponding value in `group_size`.

    Specifically, `group_size[i]` (for a 1D structure) or `group_size[i, j]` (for a 2D structure)
    defines the number of vertices in the connected component that contains vertex `i` or `(i, j)`.

    Args:
        solver (~cspuz.solver.Solver):
            The :py:class:`~cspuz.solver.Solver` object to which this constraint should be added.
        graph (Optional[Graph], optional):
            The graph on which this constraint is applied. If `shape` is specified, this must be
            omitted.
        shape (Optional[Tuple[int, int]], optional):
            The shape of the grid graph on which the constraint is applied. If `graph` is
            specified, this must be omitted.
        group_size (optional):
            The number of vertices in each connected component.

            - If `group_size` is `None`, no size restrictions are applied.
            - If `group_size` is a single value (`IntExprLike`), all components must have this
              size.
            - If `group_size` is a 1D sequence, `group_size[i]` specifies the size of the
              component containing vertex `i`.
            - If `group_size` is a 2D sequence, `group_size[i][j]` specifies the size of the
              component containing vertex `(i, j)`.

    Returns:
        IntArray1D or IntArray2D: The connected component to which each vertex belongs.
    """
    if graph is None:
        if shape is None:
            if group_size is None:
                raise ValueError("grid size cannot be inferred")
            if isinstance(group_size, Array2D):
                pass
            elif isinstance(group_size, Sequence):
                for row in group_size:
                    if not isinstance(row, Sequence):
                        raise TypeError("invalid type for 'group_size'")
            else:
                raise TypeError("invalid type for 'group_size'")
            shape = _get_array_shape_2d(group_size)  # type: ignore
        if group_size is None:
            group_size_converted: Union[None, IntExprLike, Sequence[Optional[IntExprLike]]] = None
        elif isinstance(group_size, (int, IntExpr)):
            group_size_converted = group_size
        elif isinstance(group_size, IntArray2D):
            group_size_converted = group_size.flatten().data
        else:
            group_size_converted = []
            for row in group_size:
                if row is None or isinstance(row, (int, IntExpr)):
                    raise TypeError("invalid type for 'group_size'")
                group_size_converted += row
        height, width = shape
        group_id_flat = _division_connected_variable_groups(
            solver, _grid_graph(height, width), group_size=group_size_converted
        )
        return group_id_flat.reshape(shape)
    else:
        if shape is not None:
            raise ValueError("`graph` and `shape` cannot be specified at the same time")
        return _division_connected_variable_groups(
            solver, graph, group_size=group_size  # type: ignore
        )


def _division_connected_variable_groups_with_borders(
    solver: Solver,
    graph: Graph,
    group_size: Union[IntArray1D, Sequence[Optional[IntExprLike]]],
    is_border: Sequence[BoolExprLike],
    use_graph_primitive: Optional[bool],
) -> None:
    if use_graph_primitive is None:
        use_graph_primitive = config.use_graph_division_primitive

    if len(group_size) != graph.num_vertices:
        raise ValueError(
            "group_size must have the same number of items as that of vertices in graph"
        )
    if len(is_border) != len(graph):
        raise ValueError("group_size must have the same number of items as that of edges in graph")

    if use_graph_primitive:
        solver.ensure(
            BoolExpr(
                Op.GRAPH_DIVISION,
                [graph.num_vertices, len(graph)]
                + [group_size[i] for i in range(len(group_size))]  # type: ignore
                + sum([[x, y] for x, y in graph.edges], [])  # type: ignore
                + [is_border[i] for i in range(len(is_border))],  # type: ignore
            )
        )
    else:
        group_id = _division_connected_variable_groups(solver, graph, group_size)
        for i, (u, v) in enumerate(graph):
            solver.ensure(is_border[i] == (group_id[u] != group_id[v]))


def division_connected_variable_groups_with_borders(
    solver: Solver,
    *,
    group_size: Union[
        None,
        Sequence[Optional[IntExprLike]],
        IntArray2D,
    ],
    is_border: Union[Sequence[BoolExprLike], BoolInnerGridFrame],
    graph: Optional[Graph] = None,
    use_graph_primitive: Optional[bool] = None,
) -> None:
    """Add a constraint that partitions the vertices of a graph into connected components, where
    each component has a size specified by `group_size`, and the boundaries between different
    components are specified by `is_border`.

    The constraint ensures that the vertices are divided into connected components. Different
    from :func:`division_connected_variable_groups`, this function does not explicitly number
    the connected components, but instead, the boundaries between different components are
    specified by `is_border`. The connected components are implicitly defined by the boundaries
    and the graph structure. No "extra" dividing edges are allowed: for an edge (u, v), the
    corresponding value in `is_border` must be true if and only if u and v belong to different
    connected components.

    The size of each connected component must match the corresponding value in `group_size`.

    If `graph` is specified, the constraint is applied to that graph. Otherwise, `group_size` and
    `is_border` should be specified so that the grid graph can be inferred.

    Args:
        solver (~cspuz.solver.Solver):
            The :py:class:`~cspuz.solver.Solver` object to which this constraint should be added.
        group_size (Union[None, Sequence[Optional[IntExprLike], IntArray2D], optional):
            The number of vertices in each connected component. If `None`, no size restrictions
            are applied. If a 1D sequence, `group_size[i]` specifies the size of the component
            containing vertex `i`. If a 2D sequence, `group_size[i][j]` specifies the size of the
            component containing vertex `(i, j)`.
        is_border (Union[Sequence[BoolExprLike], BoolInnerGridFrame]):
            The boundaries between different connected components. If `is_border` is a
            :class:`BoolInnerGridFrame`, the graph is automatically inferred from it.
        graph (Optional[Graph], optional):
            The graph on which this constraint is applied. If `is_border` is a
            :class:`BoolInnerGridFrame`, this is automatically inferred and should be omitted.
        use_graph_primitive (Optional[bool], optional):
            Whether primitive graph operators are used to represent this constraint. If omitted,
            the default configuration is used. Such operators are available in `enigma_csp` and
            `cspuz_core` backends.
    """
    if graph is None:
        if not isinstance(group_size, IntArray2D):
            raise TypeError("`group_size` should be an IntArray2D if graph is not specified")
        if not isinstance(is_border, BoolInnerGridFrame):
            raise TypeError("`is_border` should be a BoolInnerGridFrame if graph is not specified")

        # TODO: check that sizes are consistent
        # TODO: `group_size` can be missing (so that we can utilize "no extra border" constraint)

        group_size_flat = group_size.flatten()
        edges, graph = _from_grid_frame(is_border.dual())
        _division_connected_variable_groups_with_borders(
            solver, graph, group_size_flat, edges, use_graph_primitive
        )
    else:
        if isinstance(group_size, IntArray2D):
            raise TypeError("`group_size` should not be an IntArray2D if graph is specified")
        if isinstance(is_border, BoolInnerGridFrame):
            raise TypeError(
                "`is_border` should not be an BoolInnerGridFrame if graph is specified"
            )
        if group_size is None:
            group_size = [None for _ in range(graph.num_vertices)]
        _division_connected_variable_groups_with_borders(
            solver, graph, group_size, is_border, use_graph_primitive
        )


def _active_edges_single_cycle(
    solver: Solver,
    is_active_edge: Sequence[BoolExprLike],
    graph: Graph,
    use_graph_primitive: Optional[bool] = None,
) -> BoolArray1D:
    if use_graph_primitive is None:
        use_graph_primitive = config.use_graph_primitive
    n = graph.num_vertices

    is_passed = solver.bool_array(n)

    if use_graph_primitive:
        for i in range(n):
            degree = count_true([is_active_edge[e] for j, e in graph.incident_edges[i]])
            solver.ensure(degree == is_passed[i].cond(2, 0))

        line_graph = graph.line_graph()
        _active_vertices_connected(
            solver, is_active_edge, line_graph, acyclic=False, use_graph_primitive=True
        )
    else:
        rank = solver.int_array(n, 0, n - 1)
        is_root = solver.bool_array(n)

        for i in range(n):
            degree = count_true([is_active_edge[e] for j, e in graph.incident_edges[i]])
            solver.ensure(degree == is_passed[i].cond(2, 0))
            solver.ensure(
                is_passed[i].then(
                    count_true(
                        [
                            is_active_edge[e] & (rank[j] >= rank[i])
                            for j, e in graph.incident_edges[i]
                        ]
                    )
                    <= is_root[i].cond(2, 1)
                )
            )
        solver.ensure(count_true(is_root) == 1)
    return is_passed


@overload
def active_edges_single_cycle(
    solver: Solver, is_active_edge: BoolGridFrame, *, use_graph_primitive: Optional[bool] = None
) -> BoolArray2D: ...


@overload
def active_edges_single_cycle(
    solver: Solver,
    is_active_edge: Union[Sequence[BoolExprLike], BoolArray1D],
    graph: Graph,
    *,
    use_graph_primitive: Optional[bool] = None,
) -> BoolArray1D: ...


def active_edges_single_cycle(
    solver: Solver,
    is_active_edge: Union[BoolGridFrame, Sequence[BoolExprLike], BoolArray1D],
    graph: Optional[Graph] = None,
    *,
    use_graph_primitive: Optional[bool] = None,
) -> BoolArray1D | BoolArray2D:
    """Add a constraint that the active edges form a single cycle in the given `graph`, or there
    is no active edge.

    `is_active_edge` defines a subset of edges of `graph` (or a grid graph inferred from
    `is_active_edge`) by selecting edges with true values. This constraint ensures that the subset
    satisfies either of the following conditions:

    - The subset forms a single cycle in the graph (not necessarily spanning all vertices).
    - The subset is empty.

    If `is_active_edge` is a :class:`BoolGridFrame`, the graph is automatically inferred from it.
    In this case, `graph` should be omitted.

    Args:
        solver (~cspuz.solver.Solver):
            The :py:class:`~cspuz.solver.Solver` object to which this constraint should be added.
        is_active_edge (Union[BoolGridFrame, Sequence[BoolExprLike], BoolArray1D]):
            Sequence of boolean values or :py:class:`BoolGridFrame` representing whether
            edges are active or not.
        graph (Optional[Graph], optional):
            Graph for this constraint. If `is_active_edge` is :py:class:`BoolGridFrame`, this is
            automatically inferred and should be omitted.
        use_graph_primitive (Optional[bool], optional):
            Whether primitive graph operators are used to represent this constraint. If omitted,
            the default configuration is used. Such operators are available in `sugar`,
            `sugar_extended`, `csugar`, `enigma_csp` and `cspuz_core` backends, but depending on
            the configuration of the backend executable, they may not be supported.

    Returns:
        Union[BoolArray1D, BoolArray2D]:
            A sequence of boolean values or a 2D array representing whether each edge is passed
            by the cycle.
    """
    if graph is None:
        if not isinstance(is_active_edge, BoolGridFrame):
            raise TypeError(
                "`is_active_edge` should be a BoolGridFrame if graph is not " "specified"
            )
        edges, graph = _from_grid_frame(is_active_edge)
        is_passed_flat = _active_edges_single_cycle(
            solver, edges, graph, use_graph_primitive=use_graph_primitive
        )
        return is_passed_flat.reshape((is_active_edge.height + 1, is_active_edge.width + 1))
    else:
        if isinstance(is_active_edge, BoolGridFrame):
            raise TypeError("'is_active_edge' should be sequence-like if graph is " "specified")
        if isinstance(is_active_edge, BoolArray1D):
            is_active_edge = is_active_edge.data
        return _active_edges_single_cycle(
            solver, is_active_edge, graph, use_graph_primitive=use_graph_primitive
        )


def _active_edges_single_path(
    solver: Solver,
    is_active_edge: Sequence[BoolExprLike],
    graph: Graph,
    use_graph_primitive: Optional[bool] = None,
) -> BoolArray1D:
    if use_graph_primitive is None:
        use_graph_primitive = config.use_graph_primitive
    n = graph.num_vertices

    is_passed = solver.bool_array(n)
    is_endpoint = []

    if use_graph_primitive:
        for i in range(n):
            degree = count_true([is_active_edge[e] for j, e in graph.incident_edges[i]])
            solver.ensure(is_passed[i].then((degree == 1) | (degree == 2)))
            solver.ensure((~is_passed[i]).then(degree == 0))
            is_endpoint.append(degree == 1)
        solver.ensure(count_true(is_endpoint) == 2)
        line_graph = graph.line_graph()
        _active_vertices_connected(
            solver, is_active_edge, line_graph, acyclic=False, use_graph_primitive=True
        )
    else:
        raise RuntimeError("TODO")
    return is_passed


@overload
def active_edges_single_path(
    solver: Solver, is_active_edge: BoolGridFrame, *, use_graph_primitive: Optional[bool] = None
) -> BoolArray2D: ...


@overload
def active_edges_single_path(
    solver: Solver,
    is_active_edge: Union[Sequence[BoolExprLike], BoolArray1D],
    graph: Graph,
    *,
    use_graph_primitive: Optional[bool] = None,
) -> BoolArray1D: ...


def active_edges_single_path(
    solver: Solver,
    is_active_edge: Union[BoolGridFrame, Sequence[BoolExprLike], BoolArray1D],
    graph: Optional[Graph] = None,
    *,
    use_graph_primitive: Optional[bool] = None,
) -> BoolArray1D | BoolArray2D:
    """Add a constraint that the active edges form a single path in the given `graph`, or there
    is no active edge.

    `is_active_edge` defines a subset of edges of `graph` (or a grid graph inferred from
    `is_active_edge`) by selecting edges with true values. This constraint ensures that the subset
    satisfies either of the following conditions:

    - The subset forms a single path in the graph (not necessarily spanning all vertices).
    - The subset is empty.

    If `is_active_edge` is a :class:`BoolGridFrame`, the graph is automatically inferred from it.
    In this case, `graph` should be omitted.

    Args:
        solver (~cspuz.solver.Solver):
            The :py:class:`~cspuz.solver.Solver` object to which this constraint should be added.
        is_active_edge (Union[BoolGridFrame, Sequence[BoolExprLike], BoolArray1D]):
            Sequence of boolean values or :py:class:`BoolGridFrame` representing whether
            edges are active or not.
        graph (Optional[Graph], optional):
            Graph for this constraint. If `is_active_edge` is :py:class:`BoolGridFrame`, this is
            automatically inferred and should be omitted.
        use_graph_primitive (Optional[bool], optional):
            Whether primitive graph operators are used to represent this constraint. If omitted,
            the default configuration is used. Such operators are available in `sugar`,
            `sugar_extended`, `csugar`, `enigma_csp` and `cspuz_core` backends, but depending on
            the configuration of the backend executable, they may not be supported.

            TODO: add implementation which does not use graph primitives

    Returns:
        BoolArray1D | BoolArray2D:
            If `is_active_edge` is a :class:`BoolGridFrame`, a 2D array of boolean values
            representing whether the path passes through each vertex. Otherwise, a 1D array of
            boolean values representing whether the path passes through each vertex.
    """
    if graph is None:
        if not isinstance(is_active_edge, BoolGridFrame):
            raise TypeError(
                "`is_active_edge` should be a BoolGridFrame if graph is not " "specified"
            )
        edges, graph = _from_grid_frame(is_active_edge)
        is_passed_flat = _active_edges_single_path(
            solver, edges, graph, use_graph_primitive=use_graph_primitive
        )
        return is_passed_flat.reshape((is_active_edge.height + 1, is_active_edge.width + 1))
    else:
        if isinstance(is_active_edge, BoolGridFrame):
            raise TypeError("'is_active_edge' should be sequence-like if graph is " "specified")
        if isinstance(is_active_edge, BoolArray1D):
            is_active_edge = is_active_edge.data
        return _active_edges_single_path(
            solver, is_active_edge, graph, use_graph_primitive=use_graph_primitive
        )


def active_edges_connected_crossable(
    solver: Solver,
    is_active_edge: BoolGridFrame,
    *,
    single_cycle: bool = False,
    use_graph_primitive: Optional[bool] = None,
) -> Tuple[BoolArray2D, BoolArray2D]:  # is passed, is crossing
    """Add a constraint that the active edges form a path or cycle that may cross itself, or there
    is no active edge.

    When self-crossing is not allowed, each vertex should be incident to at most two active edges.
    On the other hand, when self-crossing is allowed, a vertex may be incident to four active
    edges, making the vertex a crossing point. On crossing points, an incoming edge goes straight
    through the crossing point.

    In this constraint, a vertex which is incident to 3 active edges is NOT allowed, even when
    it is an endpoint of the path. (TODO: allow this case)

    For example, the following is a valid path with self-crossing::

        +   +---+---+
        |   |       |
        +---+---+   +
            |   |   |
        +---+---+---+
            |   |
        +   +---+   +

    Also, the following is a valid cycle with self-crossing::

        +   +---+
            |   |
        +---+---+
        |   |
        +---+   +

    However, the following is NOT a valid path (containing two paths)::

        +   +---+
            |
        +---+---+
        |   |
        +   +---+

    The following is not allowed, either (a vertex is incident to 3 active edges)::

        +   +---+
                |
        +---+---+
        |       |
        +---+---+

    Args:
        solver (~cspuz.solver.Solver):
            The :py:class:`~cspuz.solver.Solver` object to which this constraint should be added.
        is_active_edge (~cspuz.BoolGridFrame):
            A grid frame representing whether edges are active or not.
        single_cycle (bool, optional):
            Whether the path should form a cycle. If `True` is specified, the path should form a
            cycle. Otherwise, the path should form a path or a cycle. (default: `False`)
        use_graph_primitive (Optional[bool], optional):
            Whether primitive graph operators are used to represent this constraint. If omitted,
            the default configuration is used. Such operators are available in `sugar`,
            `sugar_extended`, `csugar`, `enigma_csp` and `cspuz_core` backends, but depending on
            the configuration of the backend executable, they may not be supported.

    Returns:
        Tuple[~cspuz.BoolArray2D, ~cspuz.BoolArray2D]:
            A tuple of two :py:class:`~cspuz.BoolArray2D` objects representing whether the path
            or the cycle passes through each vertex and whether it crosses itself, respectively.
    """
    height = is_active_edge.height + 1
    width = is_active_edge.width + 1

    is_passed = solver.bool_array((height, width))
    is_cross = solver.bool_array((height, width))

    solver.ensure(is_cross.then(is_passed))

    for y in range(height):
        for x in range(width):
            if y == 0 or y == height - 1 or x == 0 or x == width - 1:
                solver.ensure(~is_cross[y, x])

            d = count_true(is_active_edge.vertex_neighbors(y, x))
            solver.ensure((~is_passed[y, x]).then(d == 0))
            solver.ensure((is_passed[y, x] & is_cross[y, x]).then(d == 4))
            if single_cycle:
                solver.ensure((is_passed[y, x] & ~is_cross[y, x]).then(d == 2))
            else:
                solver.ensure((is_passed[y, x] & ~is_cross[y, x]).then(d >= 1))
                solver.ensure((is_passed[y, x] & ~is_cross[y, x]).then(d <= 2))

    is_passed_single = solver.bool_array((height, width))
    is_passed_double_horizontal = solver.bool_array((height, width))
    is_passed_double_vertical = solver.bool_array((height, width))

    solver.ensure(is_passed_single == (is_passed & ~is_cross))
    solver.ensure(is_passed_double_horizontal == is_cross)
    solver.ensure(is_passed_double_vertical == is_cross)

    g = Graph(height * width * 3 + (height - 1) * width + height * (width - 1))
    gv = []

    for y in range(height):
        for x in range(width):
            gv.append(is_passed_single[y, x])
            gv.append(is_passed_double_horizontal[y, x])
            gv.append(is_passed_double_vertical[y, x])

    for y in range(height - 1):
        for x in range(width):
            gv.append(is_active_edge.vertical[y, x])
    for y in range(height):
        for x in range(width - 1):
            gv.append(is_active_edge.horizontal[y, x])

    for y in range(height - 1):
        for x in range(width):
            eid = height * width * 3 + y * width + x
            v0 = (y * width + x) * 3
            v1 = ((y + 1) * width + x) * 3
            g.add_edge(eid, v0)
            g.add_edge(eid, v0 + 2)
            g.add_edge(eid, v1)
            g.add_edge(eid, v1 + 2)

    for y in range(height):
        for x in range(width - 1):
            eid = height * width * 3 + (height - 1) * width + y * (width - 1) + x
            v0 = (y * width + x) * 3
            v1 = (y * width + x + 1) * 3
            g.add_edge(eid, v0)
            g.add_edge(eid, v0 + 1)
            g.add_edge(eid, v1)
            g.add_edge(eid, v1 + 1)

    active_vertices_connected(solver, gv, graph=g, use_graph_primitive=use_graph_primitive)

    return is_passed, is_cross


def active_edges_single_cycle_crossable(
    solver: Solver,
    is_active_edge: BoolGridFrame,
    *,
    use_graph_primitive: Optional[bool] = None,
) -> Tuple[BoolArray2D, BoolArray2D]:  # is passed, is crossing
    """Add a constraint that the active edges form a cycle that may cross itself, or there is no
    active edge.

    This equivalent to calling :func:`active_edges_connected_crossable` with `single_cycle=True`.

    Args:
        solver (~cspuz.solver.Solver):
            The :py:class:`~cspuz.solver.Solver` object to which this constraint should be added.
        is_active_edge (~cspuz.BoolGridFrame):
            A grid frame representing whether edges are active or not.
        use_graph_primitive (Optional[bool], optional):
            Whether primitive graph operators are used to represent this constraint. If omitted,
            the default configuration is used. Such operators are available in `sugar`,
            `sugar_extended`, `csugar`, `enigma_csp` and `cspuz_core` backends, but depending on
            the configuration of the backend executable, they may not be supported.

    Returns:
        Tuple[~cspuz.BoolArray2D, ~cspuz.BoolArray2D]:
            A tuple of two :py:class:`~cspuz.BoolArray2D` objects representing whether the cycle
            passes through each vertex and whether it crosses itself, respectively.
    """
    return active_edges_connected_crossable(
        solver, is_active_edge, single_cycle=True, use_graph_primitive=use_graph_primitive
    )
