import bpy
import random
import math
import mathutils

# Stan początkowy (aksjomat)
axiom = '-X'
# Słownik z regułami podmiany znaków
rules = {
    'F':'FF',
    'X':'F+[[X]-X]-F[-FX]+X',
    'Y': '-FX-Y',
    'C': 'F+[CF]-[CF]F',
    'G': 'F+G+F'
}

def generate_lsystem(iterations: int,axiom: str,rules: dict) -> str:
    current_string = axiom
    if iterations == 0:
        return current_string
    else:
        for i in range(iterations):
            new_string = ""
            for symbol in current_string:
                # Zamienia znak na ciąg znaków z reguł, lub zostawia ten sam jeśli reguły brak
                new_string += rules.get(symbol,symbol)
            current_string = new_string
        return current_string
    
def draw_lsystem(system_definition: str, length: float, angle: float,
                 skin: bool = False, base_radius: float = 0.4, tip_radius: float = 0.02,
                 branch_decay: float = 0.5):
    """
    Draw an L-System as 3D geometry in Blender.

    Args:
        system_definition: The L-System string to interpret.
        length: Length of each 'F' segment.
        angle: Rotation angle in degrees for '+' and '-'.
        skin: If True, apply a Skin modifier with tapering thickness.
        base_radius: Radius of the skin at the root vertex (trunk base).
        tip_radius: Minimum radius at the thinnest branch tips.
        branch_decay: Factor (0-1) by which radius shrinks when entering a branch '['.
    """
    # Przygotowanie sceny - usunięcie wszystkich istniejących obiektów
    if bpy.context.active_object:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False, confirm=False)
    # Stan i parametry "żółwia" z żółwiej grafiki
    current_pos = mathutils.Vector((0, 0, 0))
    current_rotation = 0

    # Listy przechowujące wygenerowane wierzchołki, krawędzie i informacje na temat gałęzi
    vertices = [current_pos.copy()]
    edges = []
    current_vert_index = 0
    vert_info = [(0, 0)]

    # Stos do pamiętania pozycji przy rozgałęzieniach (dla nawiasów '[' i ']')
    stack = []
    branch_depth = 0
    steps_in_branch = 0

    for symbol in system_definition:
        match symbol:
            case "F":
                # 'F' - Narysuj odcinek: obliczenie nowej pozycji po przesunięciu do przodu
                new_pos = current_pos + mathutils.Vector((length * math.sin(math.radians(current_rotation)),
                                                          0,
                                                          length * math.cos(math.radians(current_rotation))))
                steps_in_branch += 1
                vertices.append(new_pos.copy())
                new_vert_index = len(vertices) - 1
                edges.append((current_vert_index, new_vert_index))
                vert_info.append((branch_depth, steps_in_branch))
                current_pos = new_pos
                current_vert_index = new_vert_index
            case "+":
                # '+' - Obrót o kąt w lewo
                current_rotation += angle
            case "-":
                # '-' - Obrót o kąt w prawo
                current_rotation -= angle
            case "[":
                # '[' - Zapisanie obecnego stanu (początek nowej gałęzi)
                stack.append((current_pos.copy(), current_rotation, current_vert_index,
                              branch_depth, steps_in_branch))
                branch_depth += 1
                steps_in_branch = 0
            case "]":
                # ']' - Przywrócenie ostatnio zapisanego stanu (powrót po narysowaniu gałęzi)
                current_pos, current_rotation, current_vert_index, \
                    branch_depth, steps_in_branch = stack.pop()

    # Tworzenie siatki i dodawanie nowej geometrii do środowiska Blendera
    mesh = bpy.data.meshes.new("LSystem")
    mesh.from_pydata([v.to_tuple() for v in vertices], edges, [])
    mesh.update()

    obj = bpy.data.objects.new("LSystem", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Nakładanie modyfikatora "Skin" do dodania grubości roślinie
    if skin:
        obj.modifiers.new(name="Skin Modifier", type="SKIN")

        max_steps_per_depth = {}
        for depth, steps in vert_info:
            if depth not in max_steps_per_depth or steps > max_steps_per_depth[depth]:
                max_steps_per_depth[depth] = steps

        skin_data = obj.data.skin_vertices[0].data
        for i, (depth, steps) in enumerate(vert_info):
            depth_factor = branch_decay ** depth
            max_steps = max_steps_per_depth.get(depth, 1)
            if max_steps > 0:
                taper = 1.0 - 0.5 * (steps / max_steps)
            else:
                taper = 1.0
            radius = max(base_radius * depth_factor * taper, tip_radius)
            skin_data[i].radius = (radius, radius)

        obj.data.skin_vertices[0].data[0].use_root = True


system_string = generate_lsystem(0,axiom,rules)
draw_lsystem(system_string,0.5,25)
print(system_string)