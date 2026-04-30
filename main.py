import bpy
import random
import math
import mathutils

axiom = 'F'
rules = {
    # 'F': 'FF',
    'F':'G-F-G',
    'X':'F+[[X]-X]-F[-FX]+X',
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
                new_string += rules.get(symbol,symbol)
            current_string = new_string
        return current_string
    
def draw_lsystem(system_definition: str,length: float,angle: float, skin: bool = False):
    if bpy.context.active_object:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False,confirm=False)
    current_pos = mathutils.Vector((0,0,0))
    current_rotation = 0

    vertices = [current_pos.copy()] 
    edges = []
    current_vert_index = 0

    stack = []

    for symbol in system_definition:
        match symbol:
            case "F" | "G":
                new_pos = current_pos + mathutils.Vector((length * math.sin(math.radians(current_rotation)),
                                                        0,
                                                        length * math.cos(math.radians(current_rotation))))
                vertices.append(new_pos.copy())
                new_vert_index = len(vertices) - 1
                edges.append((current_vert_index, new_vert_index))
                current_pos = new_pos
                current_vert_index = new_vert_index
            case "+":
                current_rotation += angle
            case "-":
                current_rotation -= angle
            case "[":
                stack.append((current_pos.copy(), current_rotation, current_vert_index))
            case "]":
                current_pos, current_rotation, current_vert_index = stack.pop()

    mesh = bpy.data.meshes.new("LSystem")
    mesh.from_pydata([v.to_tuple() for v in vertices], edges, [])
    mesh.update()

    obj = bpy.data.objects.new("LSystem", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if skin:
        obj.modifiers.new(name="Skin Modifier",type="SKIN")
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.transform.skin_resize(value=(0.35, 0.35, 0.35))
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        mesh.vertices[0].select = True
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.transform.skin_resize(value=(2.0, 2.0, 2.0), use_proportional_edit=True, proportional_edit_falloff='SMOOTH', proportional_size=16)
        bpy.ops.object.mode_set(mode="OBJECT")
        obj.data.skin_vertices[0].data[0].use_root = True


system_string = generate_lsystem(2,axiom,rules)
draw_lsystem(system_string,0.5,90)
print(system_string)