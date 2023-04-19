import math
from shapely import Polygon

default_thickness = 4
max_point_distance = 1000


def polygonise(poly_line, thickness):

    translation_module = (
        (thickness / 2) if not math.isnan(thickness) else (default_thickness / 2)
    )

    poly_points = []
    is_first_point = True
    is_first_segment = True
    previous_point = None
    previous_quadri = None

    for point in poly_line.coords:

        if not is_first_point:

            current_segment = (previous_point, point)

            current_normale = normal(current_segment)

            # Adding the 4 new points
            if is_first_segment:
                p1 = (
                    current_segment[0][0] + current_normale[0] * translation_module,
                    current_segment[0][1] + current_normale[1] * translation_module,
                )
                p2 = (
                    current_segment[1][0] + current_normale[0] * translation_module,
                    current_segment[1][1] + current_normale[1] * translation_module,
                )
                p3 = (
                    current_segment[1][0] - current_normale[0] * translation_module,
                    current_segment[1][1] - current_normale[1] * translation_module,
                )
                p4 = (
                    current_segment[0][0] - current_normale[0] * translation_module,
                    current_segment[0][1] - current_normale[1] * translation_module,
                )

                poly_points = [p1, p2, p3, p4]
                previous_quadri = (p1, p2, p3, p4)
                is_first_segment = False
            else:

                # 4 points of the new quadri
                p1 = (
                    current_segment[0][0] + current_normale[0] * translation_module,
                    current_segment[0][1] + current_normale[1] * translation_module,
                )
                p2 = (
                    current_segment[1][0] + current_normale[0] * translation_module,
                    current_segment[1][1] + current_normale[1] * translation_module,
                )
                p3 = (
                    current_segment[1][0] - current_normale[0] * translation_module,
                    current_segment[1][1] - current_normale[1] * translation_module,
                )
                p4 = (
                    current_segment[0][0] - current_normale[0] * translation_module,
                    current_segment[0][1] - current_normale[1] * translation_module,
                )

                # Finding the correct intersection of the current quadri and the previous one
                inters1 = line_intersection(
                    (previous_quadri[0], previous_quadri[1]), (p1, p2)
                )
                inters2 = line_intersection(
                    (previous_quadri[2], previous_quadri[3]), (p3, p4)
                )

                # In some edge cases, almost straight segments create very far points.
                # In those cases, using the points of the new poly is a very fair approximation.
                inters1_distance = math.sqrt(
                    (inters1[0] - p1[0]) * (inters1[0] - p1[0])
                    + (inters1[1] - p1[1]) * (inters1[1] - p1[1])
                )
                if inters1_distance > max_point_distance:
                    inters1 = p1

                inters2_distance = math.sqrt(
                    (inters2[0] - p4[0]) * (inters2[0] - p4[0])
                    + (inters2[1] - p4[1]) * (inters2[1] - p4[1])
                )
                if inters2_distance > max_point_distance:
                    inters2 = p4

                # Merging
                middle_index = len(poly_points) // 2
                points_first_part = poly_points[: (middle_index - 1)]
                points_second_part = poly_points[(middle_index + 1) :]

                poly_points = (
                    points_first_part + [inters1, p2, p3, inters2] + points_second_part
                )

                previous_quadri = (p1, p2, p3, p4)
        else:
            is_first_point = False

        previous_point = point

    # Polygons need to be closed
    poly_points.append(poly_points[0])

    return Polygon(poly_points)


def normal(vector):
    """
    Calculates the normalized normal to the vector
    :param vector:  the vector you want to normal of
    :return: the normalized normal of the vector
    """

    dx = vector[1][0] - vector[0][0]
    dy = vector[1][1] - vector[0][1]

    normal_vector = (-dy, dx)

    normal_norm = math.sqrt(
        normal_vector[0] * normal_vector[0] + normal_vector[1] * normal_vector[1]
    )

    return (normal_vector[0] / normal_norm, normal_vector[1] / normal_norm)


def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        # Most times it's when lines are aligned and share a point.
        # In that case, returning the common point is completly valid.
        if line1[0] == line2[0] or line1[0] == line2[1]:
            return line1[0]
        elif line1[1] == line2[0] or line1[1] == line2[1]:
            return line1[1]
        else:
            # TODO: Better treatment of this: idealy should detect that the two lines are the same, and return something
            print("line_intersection: ERROR: lines do not intersect: ")
            print(str(line1))
            print(str(line2))
            return 0, 0

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y
