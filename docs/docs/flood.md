# Flood Generation

To simulate the propagation a flood, we use a graph-based pathfinding algorithm based on a rasterized grid of the height map. We first extract the digital elevation model (DEM) and rasterize it at \SI{1}{\meter\per\pixel} resolution, producing a $w\times h$ matrix $\mathbf{H}$ of the height map.
We then produce a weighted oriented graph where every node is a pixel from the height map, and we add one edge from every pixel towards each of its eight neighbours.
The weight of an edge corresponds to the slope along the direction, \ie the difference in elevation between the departing pixel and its neighbour.

Formally, this define a cost map $C$ where:

\begin{equation}
    C[(i,j), (i',j')] = \begin{cases}
        \mathbf{H}[i+u, j+v] - \mathbf{H}[i, j] & \text{for~~} (u,v) \in \{(-1, -1), (-1, 0), (-1,+1), (0, +1), (0, -1), (+1, -1), (+1, 0), (+1, +1)\}\\
        +\infty & \text{otherwise}
    \end{cases}
\end{equation}

Note that the cost is positive when moving towards a higher point, and negative when moving downhill. We then offset the cost matrix $C$ to get a matrix where all costs are non-negatives $\mathbf{C} = C + \min(C)$.

Pixels that are covered by a water mass that will act as the source of the flood are tagged as 1 in binary matrix $\mathbf{S}$ of dimensions $w\times h$.

Finally, for each source $s$, we apply the Dijkstra to find the shortest path between $s$ and every point $(i,j)$ in the raster, \ie every node in the graph. If the total length of the path $l_{i,j}$ from the source to $(i,j)$ is under a threshold $L$, $(i,j)$ is then tagged as being flooded by the source $s$. The height of the flood is obtained by:

\begin{equation}
    \text{water height}[i,j] = \underbrace{h \cdot (L - l_{i,j})^2}_{\text{relative water height, between 0 and } h} + \underbrace{\mathbf{H}(s)}_{\text{source height}}
\end{equation}

Note that in this equation, the final water height might be inferior to the terrain height $\mathbf{H}[i,j]$. In that case, we consider that pixel $(i,j)$ is actually not flooded.