import math
from itertools import combinations

# --- Geometric Helper Functions ---

def distance_sq(p1, p2):
    """Calculates the squared distance between two points."""
    return (p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2

def on_segment(p, q, r):
    """Given three collinear points p, q, r, checks if point q lies on line segment 'pr'."""
    return (q['x'] <= max(p['x'], r['x']) and q['x'] >= min(p['x'], r['x']) and
            q['y'] <= max(p['y'], r['y']) and q['y'] >= min(p['y'], r['y']))

def orientation(p, q, r):
    """Finds orientation of ordered triplet (p, q, r).
    Returns:
    0 --> p, q and r are collinear
    1 --> Clockwise
    2 --> Counterclockwise
    """
    val = (q['y'] - p['y']) * (r['x'] - q['x']) - \
          (q['x'] - p['x']) * (r['y'] - q['y'])
    if val == 0: return 0  # Collinear
    return 1 if val > 0 else 2  # Clockwise or Counter-clockwise

def segments_intersect(p1, q1, p2, q2):
    """Checks if line segment 'p1q1' and 'p2q2' intersect."""
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # General case: segments cross each other
    if o1 != o2 and o3 != o4:
        return True

    # Special Cases for collinear points
    # p1, q1 and p2 are collinear and p2 lies on segment p1q1
    if o1 == 0 and on_segment(p1, p2, q1): return True
    # p1, q1 and q2 are collinear and q2 lies on segment p1q1
    if o2 == 0 and on_segment(p1, q2, q1): return True
    # p2, q2 and p1 are collinear and p1 lies on segment p2q2
    if o3 == 0 and on_segment(p2, p1, q2): return True
    # p2, q2 and q1 are collinear and q1 lies on segment p2q2
    if o4 == 0 and on_segment(p2, q1, q2): return True

    return False

def get_segment_intersection_point(p1, q1, p2, q2):
    """Finds the intersection point of two line segments 'p1q1' and 'p2q2'.
    Returns a dict {'x', 'y'} or None if they do not intersect on the segments.
    """
    x1, y1 = p1['x'], p1['y']
    x2, y2 = q1['x'], q1['y']
    x3, y3 = p2['x'], p2['y']
    x4, y4 = q2['x'], q2['y']

    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if den == 0:
        return None  # Lines are parallel or collinear

    t_num = (x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)
    u_num = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3))

    t = t_num / den
    u = u_num / den

    # If 0<=t<=1 and 0<=u<=1, the segments intersect
    if 0 <= t <= 1 and 0 <= u <= 1:
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return {'x': ix, 'y': iy}

    return None  # Intersection point is not on both segments


def is_ray_blocked(p_start, p_end, fissures, barricades, scorched_zones=None):
    """Checks if a segment is blocked by a fissure, barricade, or scorched zone."""
    obstacles = (fissures or []) + (barricades or [])
    for obstacle in obstacles:
        if get_segment_intersection_point(p_start, p_end, obstacle['p1'], obstacle['p2']):
            return True
    
    if scorched_zones:
        for zone in scorched_zones:
            if len(zone['points']) == 3:
                p1, p2, p3 = zone['points']
                # Check intersection with any of the 3 edges of the triangle
                if (get_segment_intersection_point(p_start, p_end, p1, p2) or
                    get_segment_intersection_point(p_start, p_end, p2, p3) or
                    get_segment_intersection_point(p_start, p_end, p3, p1)):
                    return True

    return False


def get_extended_border_point(p1, p2, grid_size, fissures, barricades, scorched_zones=None):
    """
    Extends a line segment p1-p2 from p1 outwards through p2 to the border.
    Returns the border point dictionary or None.
    """
    x1, y1 = p1['x'], p1['y']
    x2, y2 = p2['x'], p2['y']
    dx, dy = x2 - x1, y2 - y1

    if dx == 0 and dy == 0: return None

    # Check if extension is blocked
    # Create a very long ray for intersection test
    ray_end_point = {'x': p2['x'] + dx * grid_size * 2, 'y': p2['y'] + dy * grid_size * 2}
    if is_ray_blocked(p2, ray_end_point, fissures, barricades, scorched_zones):
        return None # Extension is blocked

    # We are calculating p_new = p1 + t * (p2 - p1) for t > 1
    t_values = []
    if dx != 0:
        t_values.append((0 - x1) / dx)
        t_values.append((grid_size - 1 - x1) / dx)
    if dy != 0:
        t_values.append((0 - y1) / dy)
        t_values.append((grid_size - 1 - y1) / dy)

    # Use a small epsilon to avoid floating point issues with the point itself
    valid_t = [t for t in t_values if t > 1.0001]
    if not valid_t: return None

    t = min(valid_t)
    ix, iy = x1 + t * dx, y1 + t * dy
    ix = round(max(0, min(grid_size - 1, ix)))
    iy = round(max(0, min(grid_size - 1, iy)))
    return {"x": ix, "y": iy}


def reflect_point(point, p1_axis, p2_axis):
    """Reflects a point across the line defined by p1_axis and p2_axis."""
    px, py = point['x'], point['y']
    x1, y1 = p1_axis['x'], p1_axis['y']
    x2, y2 = p2_axis['x'], p2_axis['y']

    # Line equation ax + by + c = 0
    a = y2 - y1
    b = x1 - x2
    
    if a == 0 and b == 0: # The axis points are the same, no line.
        return None

    c = -a * x1 - b * y1
    
    den = a**2 + b**2
    if den == 0: return None
    
    val = -2 * (a * px + b * py + c) / den
    
    rx = px + val * a
    ry = py + val * b
    
    return {'x': rx, 'y': ry}

def is_rectangle(p1, p2, p3, p4):
    """Checks if four points form a rectangle. Returns (is_rect, aspect_ratio).
    This is a helper function that doesn't rely on game state.
    """
    points = [p1, p2, p3, p4]
    
    # Check for non-collapsed points. Using tuple of coords for hashability.
    if len(set((p['x'], p['y']) for p in points)) < 4:
        return False, 0

    # There are 6 distances between 4 points.
    dists_sq = sorted([
        distance_sq(p1, p2), distance_sq(p1, p3), distance_sq(p1, p4),
        distance_sq(p2, p3), distance_sq(p2, p4), distance_sq(p3, p4)
    ])

    # For a rectangle, the sorted squared distances should be [s1, s1, s2, s2, d, d]
    # where s1 and s2 are sides and d is the diagonal.
    s1_sq, s2_sq = dists_sq[0], dists_sq[2]
    d_sq = dists_sq[4]

    # Check for non-zero side length
    if s1_sq < 0.01:
        return False, 0
    
    # Check for 2 pairs of equal sides (with a small tolerance for float issues)
    if not (abs(dists_sq[0] - dists_sq[1]) < 0.01 and abs(dists_sq[2] - dists_sq[3]) < 0.01):
        return False, 0
    
    # Check for 2 equal diagonals
    if not abs(dists_sq[4] - dists_sq[5]) < 0.01:
        return False, 0
    
    # Check Pythagorean theorem for a right angle: s1^2 + s2^2 = d^2
    if not abs((s1_sq + s2_sq) - d_sq) < 0.01:
        return False, 0

    # Calculate aspect ratio (long side / short side)
    side1 = math.sqrt(s1_sq)
    side2 = math.sqrt(s2_sq)
    
    # This check is redundant due to the s1_sq check above, but safe.
    if side1 < 0.1 or side2 < 0.1: return False, 0

    aspect_ratio = max(side1, side2) / min(side1, side2)
    
    return True, aspect_ratio

def is_parallelogram(p1, p2, p3, p4):
    """Checks if four points form a parallelogram. Returns (is_para, is_rect)."""
    points = [p1, p2, p3, p4]
    if len(set((p['x'], p['y']) for p in points)) < 4:
        return False, False

    dists_sq = sorted([
        distance_sq(p1, p2), distance_sq(p1, p3), distance_sq(p1, p4),
        distance_sq(p2, p3), distance_sq(p2, p4), distance_sq(p3, p4)
    ])

    # Check for 2 pairs of equal sides
    if not (abs(dists_sq[0] - dists_sq[1]) < 0.01 and abs(dists_sq[2] - dists_sq[3]) < 0.01):
        return False, False
    
    s1_sq, s2_sq = dists_sq[0], dists_sq[2]
    d1_sq, d2_sq = dists_sq[4], dists_sq[5]

    # Check parallelogram property: 2*(s1^2 + s2^2) = d1^2 + d2^2
    if not abs(2 * (s1_sq + s2_sq) - (d1_sq + d2_sq)) < 0.1: # Increased tolerance
        return False, False
        
    # Check if it's a rectangle
    is_rect = abs(d1_sq - d2_sq) < 0.01
    
    return True, is_rect

def get_isosceles_triangle_info(p1, p2, p3):
    """
    Checks if 3 points form an isosceles triangle.
    Returns a dict with {'apex': point, 'base': [p_b1, p_b2], 'height_sq': h^2} or None.
    The apex is the vertex where the two equal sides meet.
    """
    dists = {
        '12': distance_sq(p1, p2),
        '13': distance_sq(p1, p3),
        '23': distance_sq(p2, p3),
    }
    
    TOLERANCE = 0.01 # Using a small tolerance for float equality

    # Check for non-degenerate triangles
    if dists['12'] < TOLERANCE or dists['13'] < TOLERANCE or dists['23'] < TOLERANCE:
        return None

    # Check for two equal sides
    if abs(dists['12'] - dists['13']) < TOLERANCE:
        height_sq = dists['12'] - (dists['23'] / 4.0)
        return {'apex': p1, 'base': [p2, p3], 'height_sq': height_sq, 'leg_sq': dists['12']}
    elif abs(dists['12'] - dists['23']) < TOLERANCE:
        height_sq = dists['12'] - (dists['13'] / 4.0)
        return {'apex': p2, 'base': [p1, p3], 'height_sq': height_sq, 'leg_sq': dists['12']}
    elif abs(dists['13'] - dists['23']) < TOLERANCE:
        height_sq = dists['13'] - (dists['12'] / 4.0)
        return {'apex': p3, 'base': [p1, p2], 'height_sq': height_sq, 'leg_sq': dists['13']}
    
    return None

def polygon_area(points):
    """Calculates area of a polygon using Shoelace formula."""
    if len(points) < 3:
        return 0
    area = 0.0
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        area += points[i]['x'] * points[j]['y']
        area -= points[j]['x'] * points[i]['y']
    return abs(area) / 2.0

def is_point_inside_triangle(point, tri_p1, tri_p2, tri_p3):
    """Checks if a point is inside a triangle defined by three other points."""
    main_area = polygon_area([tri_p1, tri_p2, tri_p3])
    if main_area < 0.01: # Degenerate triangle
        return False

    area1 = polygon_area([point, tri_p2, tri_p3])
    area2 = polygon_area([tri_p1, point, tri_p3])
    area3 = polygon_area([tri_p1, tri_p2, point])
    
    # Check if sum of sub-triangle areas equals the main triangle area (with tolerance)
    return abs((area1 + area2 + area3) - main_area) < 0.01

def is_regular_pentagon(p1, p2, p3, p4, p5):
    """Checks if five points form a regular pentagon."""
    points = [p1, p2, p3, p4, p5]
    if len(set((p['x'], p['y']) for p in points)) < 5:
        return False

    # Calculate all 10 squared distances between the 5 points.
    dists_sq = sorted([distance_sq(pi, pj) for pi, pj in combinations(points, 2)])
    
    # A regular pentagon has 5 equal sides (shortest distance) and 5 equal diagonals (next shortest).
    side_sq = dists_sq[0]
    diag_sq = dists_sq[5]

    # Check for 5 equal sides
    if not all(abs(d - side_sq) < 0.01 for d in dists_sq[0:5]):
        return False

    # Check for 5 equal diagonals
    if not all(abs(d - diag_sq) < 0.01 for d in dists_sq[5:10]):
        return False
        
    # Check the golden ratio property: diag^2 / side^2 = phi^2
    # phi^2 = ((1+sqrt(5))/2)^2 = (3+sqrt(5))/2 ~= 2.618034
    if side_sq < 0.01: return False # Not a real pentagon
    ratio_sq = diag_sq / side_sq
    
    phi_sq = ((1 + math.sqrt(5)) / 2)**2
    if abs(ratio_sq - phi_sq) > 0.05: # Allow some tolerance for float inaccuracies
        return False
        
    return True

def points_centroid(points):
    """Calculates the geometric centroid of a list of points."""
    if not points:
        return None
    num_points = len(points)
    x_sum = sum(p['x'] for p in points)
    y_sum = sum(p['y'] for p in points)
    return {'x': x_sum / num_points, 'y': y_sum / num_points}


def polygon_perimeter(points):
    """Calculates the perimeter of a polygon."""
    perimeter = 0.0
    n = len(points)
    for i in range(n):
        p1 = points[i]
        p2 = points[(i + 1) % n]
        perimeter += math.sqrt(distance_sq(p1, p2))
    return perimeter


def get_convex_hull(points):
    """Computes the convex hull of a set of points using Graham Scan."""
    if len(points) < 3:
        return points
    
    # Find pivot (lowest y, then lowest x)
    pivot = min(points, key=lambda p: (p['y'], p['x']))
    
    # Sort points by polar angle with pivot
    sorted_points = sorted(
        [p for p in points if p != pivot], 
        key=lambda p: (math.atan2(p['y'] - pivot['y'], p['x'] - pivot['x']), distance_sq(p, pivot))
    )
    
    hull = [pivot]
    for p in sorted_points:
        while len(hull) >= 2 and orientation(hull[-2], hull[-1], p) != 2: # 2 = counter-clockwise
            hull.pop()
        hull.append(p)
        
    return hull


def is_spawn_location_valid(new_point_coords, new_point_teamId, grid_size, all_points, fissures, heartwoods, scorched_zones=None, min_dist_sq=1.0):
    """Checks if a new point can be spawned at the given coordinates."""
    # Check if point is within grid boundaries
    if not (0 <= new_point_coords['x'] < grid_size and 0 <= new_point_coords['y'] < grid_size):
        return False, 'outside of grid boundaries'

    # Check proximity to existing points
    for existing_p in all_points.values():
        if distance_sq(new_point_coords, existing_p) < min_dist_sq:
            return False, 'too close to an existing point'
    
    # Check proximity to fissures (a simple bounding box check for performance)
    for fissure in fissures:
        p1 = fissure['p1']
        p2 = fissure['p2']
        # Bounding box of the fissure segment
        box_x_min = min(p1['x'], p2['x']) - 1
        box_x_max = max(p1['x'], p2['x']) + 1
        box_y_min = min(p1['y'], p2['y']) - 1
        box_y_max = max(p1['y'], p2['y']) + 1
        
        if (new_point_coords['x'] >= box_x_min and new_point_coords['x'] <= box_x_max and
            new_point_coords['y'] >= box_y_min and new_point_coords['y'] <= box_y_max):
            # A more precise check can be done here if needed, but this is a good first pass
            return False, 'too close to a fissure'

    # Check against enemy Heartwood defensive aura
    if heartwoods:
        for teamId, heartwood in heartwoods.items():
            if teamId != new_point_teamId:
                aura_radius_sq = (grid_size * 0.2)**2
                if distance_sq(new_point_coords, heartwood['center_coords']) < aura_radius_sq:
                    return False, 'blocked by an enemy Heartwood aura'

    # Check against scorched zones
    if scorched_zones:
        for zone in scorched_zones:
            if len(zone['points']) == 3:
                if is_point_inside_triangle(new_point_coords, zone['points'][0], zone['points'][1], zone['points'][2]):
                    return False, 'inside a scorched zone'
    
    return True, 'valid'