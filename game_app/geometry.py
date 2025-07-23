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


def is_ray_blocked(p_start, p_end, fissures, barricades):
    """Checks if a segment is blocked by a fissure or barricade."""
    for fissure in fissures:
        if get_segment_intersection_point(p_start, p_end, fissure['p1'], fissure['p2']):
            return True
    for barricade in barricades:
        if get_segment_intersection_point(p_start, p_end, barricade['p1'], barricade['p2']):
            return True
    return False


def get_extended_border_point(p1, p2, grid_size, fissures, barricades):
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
    if is_ray_blocked(p2, ray_end_point, fissures, barricades):
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
    ix, iy = x1 + t * dx, y1 + t * iy
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