bl_info = {
    "name": "L-System 3D Generator",
    "author": "Piotr Gruchala",
    "version": (1, 0, 0),
    "blender": (5, 1, 0),
    "location": "View3D > Sidebar > L-System",
    "description": "Generate 3D L-System plants with skin, leaves, and flowers",
    "category": "Add Mesh",
}

import bpy
import random
import math
import mathutils
from bpy.props import (
    StringProperty, IntProperty, FloatProperty, BoolProperty,
    EnumProperty, FloatVectorProperty,
)

_PRESETS = {
    'DAISY': {
        'name': 'Five-Petal Daisy',
        'axiom': 'SSSSA',
        'rules_str': 'A=[P]//[P]//[P]//[P]//[P]C;P=&&FF[+F][-F]FF;C=FFFF;S=FF[^L][\\\\\\\\\\^L];L=F[+F][-F];F=FF',
        'angle': 36, 'roll_angle': 0.0, 'use_custom_roll': False,
        'iterations': 3, 'length': 0.3,
        'skin': True, 'base_radius': 0.15, 'tip_radius': 0.005, 'branch_decay': 0.6,
        'randomize': 0.0, 'seed': 0,
        'leaves': True, 'leaf_size': 0.08,
        'flowers': True, 'flower_size': 0.10, 'flower_petals': 5, 'flower_probability': 1.0,
    },
    'SHRUB': {
        'name': 'Self-Similar Shrub',
        'axiom': 'X',
        'rules_str': 'X=F+[P+Q][-Q]F[+FQ]-Q;P=FF;Q=F[+Z]F[-Z]FZ;Z=[+F-F-F+|+F-F-F];F=FF',
        'angle': 25, 'roll_angle': 0.0, 'use_custom_roll': False,
        'iterations': 4, 'length': 0.25,
        'skin': True, 'base_radius': 0.20, 'tip_radius': 0.005, 'branch_decay': 0.55,
        'randomize': 0.15, 'seed': 0,
        'leaves': True, 'leaf_size': 0.10,
        'flowers': True, 'flower_size': 0.08, 'flower_petals': 5, 'flower_probability': 0.3,
    },
    'GOLDEN': {
        'name': 'Golden-Angle Spiral',
        'axiom': 'A',
        'rules_str': 'A=[&B]/A;B=F[+F][-F]^^F[+F]F;F=FF',
        'angle': 25, 'roll_angle': 137.5, 'use_custom_roll': True,
        'iterations': 7, 'length': 0.15,
        'skin': True, 'base_radius': 0.25, 'tip_radius': 0.005, 'branch_decay': 0.5,
        'randomize': 0.1, 'seed': 0,
        'leaves': True, 'leaf_size': 0.10,
        'flowers': True, 'flower_size': 0.08, 'flower_petals': 5, 'flower_probability': 0.25,
    },
    'FRACTAL_PLANT': {
        'name': 'Fractal Plant',
        'axiom': 'X',
        'rules_str': 'X=F+[[X]-X]-F[-FX]+X;F=FF',
        'angle': 25, 'roll_angle': 0.0, 'use_custom_roll': False,
        'iterations': 6, 'length': 0.15,
        'skin': False, 'base_radius': 0.05, 'tip_radius': 0.005, 'branch_decay': 0.5,
        'randomize': 0.0, 'seed': 0,
        'leaves': False, 'leaf_size': 0.06,
        'flowers': False, 'flower_size': 0.08, 'flower_petals': 5, 'flower_probability': 0.0,
    },
    'SIERPINSKI': {
        'name': 'Sierpinski Triangle',
        'axiom': 'F-G-G',
        'rules_str': 'F=F-G+F+G-F;G=GG',
        'angle': 120, 'roll_angle': 0.0, 'use_custom_roll': False,
        'iterations': 6, 'length': 0.1,
        'skin': False, 'base_radius': 0.05, 'tip_radius': 0.005, 'branch_decay': 0.5,
        'randomize': 0.0, 'seed': 0,
        'leaves': False, 'leaf_size': 0.08,
        'flowers': False, 'flower_size': 0.08, 'flower_petals': 5, 'flower_probability': 0.0,
    },
    'KOCH': {
        'name': "Koch's Snowflake",
        'axiom': 'F--F--F',
        'rules_str': 'F=F+F--F+F',
        'angle': 60, 'roll_angle': 0.0, 'use_custom_roll': False,
        'iterations': 4, 'length': 0.15,
        'skin': False, 'base_radius': 0.05, 'tip_radius': 0.005, 'branch_decay': 0.5,
        'randomize': 0.0, 'seed': 0,
        'leaves': False, 'leaf_size': 0.08,
        'flowers': False, 'flower_size': 0.08, 'flower_petals': 5, 'flower_probability': 0.0,
    },
    'DRAGON': {
        'name': 'Dragon Curve',
        'axiom': 'FX',
        'rules_str': 'X=X+YF+;Y=-FX-Y',
        'angle': 90, 'roll_angle': 0.0, 'use_custom_roll': False,
        'iterations': 10, 'length': 0.15,
        'skin': False, 'base_radius': 0.05, 'tip_radius': 0.005, 'branch_decay': 0.5,
        'randomize': 0.0, 'seed': 0,
        'leaves': False, 'leaf_size': 0.08,
        'flowers': False, 'flower_size': 0.08, 'flower_petals': 5, 'flower_probability': 0.0,
    },
}


def _parse_rules(rules_str: str) -> dict:
    """Parsuje zasady oddzielone za pomocą średnika do słownika.

    Format: ``A=[P]//[P];P=&&FF;F=FF``
    """
    rules = {}
    for token in rules_str.split(';'):
        token = token.strip()
        if '=' in token:
            lhs, rhs = token.split('=', 1)
            rules[lhs.strip()] = rhs
    return rules

def generate_lsystem(iterations: int, axiom: str, rules: dict) -> str:
    """Stosuje zasady L-systemu tworząc łańcuch znaków przez określoną ilość iteracji."""
    current_string = axiom
    for _ in range(iterations):
        current_string = "".join(rules.get(symbol, symbol) for symbol in current_string)
    return current_string

def _rotation_matrix(axis, angle_deg):
    return mathutils.Matrix.Rotation(math.radians(angle_deg), 3, axis)

def _orientation_to_4x4(orientation, position):
    mat = orientation.to_4x4()
    mat.translation = position
    return mat


def _create_material(name, color):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = color
    return mat


def _create_leaf_mesh(size=0.15):
    s = size
    verts = [(0, 0, 0), (-s * 0.4, s * 0.5, 0), (0, s, 0), (s * 0.4, s * 0.5, 0)]
    faces = [(0, 1, 2, 3)]
    mesh = bpy.data.meshes.new("LeafMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


def _create_flower_mesh(radius=0.12, petals=5):
    verts = [(0, 0, 0)]
    faces = []
    for i in range(petals):
        a1 = math.radians(i * 360 / petals)
        a2 = math.radians((i + 0.5) * 360 / petals)
        a3 = math.radians((i + 1) * 360 / petals)
        verts.append((math.cos(a1) * radius * 0.3, 0, math.sin(a1) * radius * 0.3))
        verts.append((math.cos(a2) * radius, radius * 0.1, math.sin(a2) * radius))
        verts.append((math.cos(a3) * radius * 0.3, 0, math.sin(a3) * radius * 0.3))
        base = 1 + i * 3
        faces.append((0, base, base + 1, base + 2))
    mesh = bpy.data.meshes.new("FlowerMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


def draw_lsystem_3d(system_definition, length, angle,
                    skin=False, base_radius=0.4,
                    tip_radius=0.02, branch_decay=0.5,
                    randomize=0.0, seed=None,
                    leaves=False, leaf_size=0.15,
                    flowers=False, flower_size=0.12,
                    flower_petals=5, flower_probability=0.3,
                    roll_angle=None, clean_scene=False):
    """Interpretuje L-system i tworzy na jego podstawie geometrię w Blenderze."""
    effective_roll_angle = roll_angle if roll_angle is not None else angle
    rng = random.Random(seed)

    def _perturb(base_angle): #Losowe odchylenie w oparciu o podany kąt.
        if randomize <= 0.0:
            return base_angle
        return base_angle * (1.0 + rng.uniform(-1.0, 1.0) * randomize)

    if clean_scene:
        if bpy.context.active_object:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False, confirm=False)

    # Stan żółwia
    current_pos = mathutils.Vector((0, 0, 0))
    heading = mathutils.Vector((0, 0, 1))
    up = mathutils.Vector((0, 1, 0))
    right = mathutils.Vector((1, 0, 0))
    orientation = mathutils.Matrix((right, heading, up)).transposed()
    current_length = length

    vertices = [current_pos.copy()]
    edges = []
    current_vert_index = 0
    vert_info = [(0, 0)]
    stack = []
    branch_depth = 0
    steps_in_branch = 0
    drew_in_branch = False
    tip_data = []

    for symbol in system_definition:
        local_right = mathutils.Vector(orientation.col[0])
        local_heading = mathutils.Vector(orientation.col[1])
        local_up = mathutils.Vector(orientation.col[2])

        match symbol:
            case "F" | "G":
                new_pos = current_pos + local_heading * current_length
                steps_in_branch += 1
                drew_in_branch = True
                vertices.append(new_pos.copy())
                new_vert_index = len(vertices) - 1
                edges.append((current_vert_index, new_vert_index))
                vert_info.append((branch_depth, steps_in_branch))
                current_pos = new_pos
                current_vert_index = new_vert_index
            case "+":
                rot = _rotation_matrix(local_up, _perturb(angle))
                orientation = rot @ orientation
            case "-":
                rot = _rotation_matrix(local_up, -_perturb(angle))
                orientation = rot @ orientation
            case "^":
                rot = _rotation_matrix(local_right, _perturb(angle))
                orientation = rot @ orientation
            case "&":
                rot = _rotation_matrix(local_right, -_perturb(angle))
                orientation = rot @ orientation
            case "\\":
                rot = _rotation_matrix(local_heading, _perturb(effective_roll_angle))
                orientation = rot @ orientation
            case "/":
                rot = _rotation_matrix(local_heading, -_perturb(effective_roll_angle))
                orientation = rot @ orientation
            case "|":
                rot = _rotation_matrix(local_up, 180)
                orientation = rot @ orientation
            case "!":
                current_length *= 0.9
            case "[":
                stack.append((
                    current_pos.copy(), orientation.copy(), current_vert_index,
                    branch_depth, steps_in_branch, current_length, drew_in_branch,
                ))
                branch_depth += 1
                steps_in_branch = 0
                drew_in_branch = False
            case "]":
                if drew_in_branch and (leaves or flowers):
                    tip_data.append((current_pos.copy(), orientation.copy()))
                (current_pos, orientation, current_vert_index,
                 branch_depth, steps_in_branch, current_length,
                 drew_in_branch) = stack.pop()

    # budowanie siatki
    mesh = bpy.data.meshes.new("LSystem3D")
    mesh.from_pydata([v.to_tuple() for v in vertices], edges, [])
    mesh.update()

    obj = bpy.data.objects.new("LSystem3D", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    stem_mat = bpy.data.materials.get("StemMaterial")
    if stem_mat is None:
        stem_mat = bpy.data.materials.new("StemMaterial")
        stem_mat.use_nodes = True
    obj.data.materials.append(stem_mat)

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
            taper = 1.0 - 0.5 * (steps / max_steps) if max_steps > 0 else 1.0
            radius = max(base_radius * depth_factor * taper, tip_radius)
            skin_data[i].radius = (radius, radius)
        skin_data[0].use_root = True

    created_objects = [obj]
    if (leaves or flowers) and tip_data:
        leaf_mesh = _create_leaf_mesh(leaf_size) if leaves else None
        flower_mesh = _create_flower_mesh(flower_size, flower_petals) if flowers else None
        leaf_mat = _create_material("LeafMaterial", (0.15, 0.55, 0.10, 1.0)) if leaves else None
        flower_mat = _create_material("FlowerMaterial", (0.85, 0.25, 0.40, 1.0)) if flowers else None

        for idx, (tip_pos, tip_orient) in enumerate(tip_data):
            place_flower = flowers and rng.random() < flower_probability
            place_leaf = leaves
            if place_leaf:
                leaf_obj = bpy.data.objects.new(f"Leaf_{idx}", leaf_mesh.copy())
                leaf_obj.matrix_world = _orientation_to_4x4(tip_orient, tip_pos)
                leaf_obj.rotation_euler.rotate_axis('Y', rng.uniform(0, math.tau))
                leaf_obj.data.materials.append(leaf_mat)
                bpy.context.collection.objects.link(leaf_obj)
                leaf_obj.parent = obj
                created_objects.append(leaf_obj)
            if place_flower:
                fl_obj = bpy.data.objects.new(f"Flower_{idx}", flower_mesh.copy())
                flower_pos = tip_pos + mathutils.Vector(tip_orient.col[1]) * leaf_size * 0.5
                fl_obj.matrix_world = _orientation_to_4x4(tip_orient, flower_pos)
                fl_obj.rotation_euler.rotate_axis('Y', rng.uniform(0, math.tau))
                fl_obj.data.materials.append(flower_mat)
                bpy.context.collection.objects.link(fl_obj)
                fl_obj.parent = obj
                created_objects.append(fl_obj)

    return created_objects

class LSystemProperties(bpy.types.PropertyGroup):
    pass


LSystemProperties.__annotations__["preset"] = EnumProperty(
    name="Preset",
    items=[
        ('CUSTOM', "Custom", "Use custom axiom and rules"),
        ('DAISY', "Five-Petal Radial Daisy", "Classic daisy with 5 petals"),
        ('SHRUB', "Branching Shrub", "Self-similar fractal bush"),
        ('GOLDEN', "Golden-Angle Spiral", "Phyllotaxis spiral pattern"),
        ('FRACTAL_PLANT', "Fractal Plant", "Classic fractal plant with branching"),
        ('SIERPINSKI', "Sierpinski Triangle", "Sierpinski triangle fractal"),
        ('KOCH', "Koch's Snowflake", "Koch snowflake curve"),
        ('DRAGON', "Dragon Curve", "Classic dragon curve fractal"),
    ],
    default='DAISY',
    description="Choose a preset or define custom rules",
)

LSystemProperties.__annotations__["axiom"] = StringProperty(
    name="Axiom", default="SSSSA", description="Starting string",
)
LSystemProperties.__annotations__["rules_str"] = StringProperty(
    name="Rules",
    default="A=[P]//[P]//[P]//[P]//[P]C;P=&&FF[+F][-F]FF;C=FFFF;S=FF[^L][\\\\\\\\\\^L];L=F[+F][-F];F=FF",
    description="Production rules (semicolon-separated, e.g. A=F[+A];F=FF)",
)
LSystemProperties.__annotations__["iterations"] = IntProperty(
    name="Iterations", default=3, min=1, max=20, description="Number of rewriting iterations",
)
LSystemProperties.__annotations__["length"] = FloatProperty(
    name="Segment Length", default=0.3, min=0.01, max=5.0, step=1, precision=3,
)
LSystemProperties.__annotations__["angle"] = FloatProperty(
    name="Angle", default=36.0, min=0.0, max=360.0, step=100, precision=1,
    description="Turn angle for +, -, ^, & (degrees)",
)
LSystemProperties.__annotations__["use_custom_roll"] = BoolProperty(
    name="Custom Roll Angle", default=False,
    description="Use a different angle for roll (/ and \\)",
)
LSystemProperties.__annotations__["roll_angle"] = FloatProperty(
    name="Roll Angle", default=36.0, min=0.0, max=360.0, step=100, precision=1,
    description="Roll angle for / and \\ (degrees)",
)
LSystemProperties.__annotations__["seed"] = IntProperty(
    name="Seed", default=0, min=0, description="Random seed (0 = no fixed seed)",
)

LSystemProperties.__annotations__["skin"] = BoolProperty(name="Skin Modifier", default=True)
LSystemProperties.__annotations__["base_radius"] = FloatProperty(
    name="Base Radius", default=0.15, min=0.001, max=2.0, step=1, precision=3,
)
LSystemProperties.__annotations__["tip_radius"] = FloatProperty(
    name="Tip Radius", default=0.005, min=0.001, max=1.0, step=1, precision=3,
)
LSystemProperties.__annotations__["branch_decay"] = FloatProperty(
    name="Branch Decay", default=0.6, min=0.01, max=1.0, step=1, precision=2,
)

LSystemProperties.__annotations__["randomize"] = FloatProperty(
    name="Randomize", default=0.0, min=0.0, max=1.0, step=1, precision=2,
    description="Angle perturbation amount",
)

LSystemProperties.__annotations__["leaves"] = BoolProperty(name="Leaves", default=True)
LSystemProperties.__annotations__["leaf_size"] = FloatProperty(
    name="Leaf Size", default=0.08, min=0.01, max=1.0, step=1, precision=3,
)

LSystemProperties.__annotations__["flowers"] = BoolProperty(name="Flowers", default=True)
LSystemProperties.__annotations__["flower_size"] = FloatProperty(
    name="Flower Size", default=0.10, min=0.01, max=1.0, step=1, precision=3,
)
LSystemProperties.__annotations__["flower_petals"] = IntProperty(name="Petals", default=5, min=3, max=20)
LSystemProperties.__annotations__["flower_probability"] = FloatProperty(
    name="Flower Prob.", default=1.0, min=0.0, max=1.0, step=1, precision=2,
)

LSystemProperties.__annotations__["clean_scene"] = BoolProperty(
    name="Clean Scene First", default=True,
    description="Delete all objects before generating",
)

class LSYSTEM_OT_generate(bpy.types.Operator):
    """Generate the L-System plant"""
    bl_idname = "lsystem.generate"
    bl_label = "Generate L-System"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.lsystem_props

        if props.preset != 'CUSTOM' and props.preset in _PRESETS:
            p = _PRESETS[props.preset]
            axiom = p['axiom']
            rules = _parse_rules(p['rules_str'])
            angle = p['angle']
            roll_angle = p['roll_angle'] if p['use_custom_roll'] else None
            iterations = p['iterations']
            length = p['length']
            skin = p['skin']
            base_radius = p['base_radius']
            tip_radius = p['tip_radius']
            branch_decay = p['branch_decay']
            randomize = p['randomize']
            seed_val = p['seed'] if p['seed'] != 0 else None
            leaves = p['leaves']
            leaf_size = p['leaf_size']
            flowers = p['flowers']
            flower_size = p['flower_size']
            flower_petals = p['flower_petals']
            flower_probability = p['flower_probability']
        else:
            axiom = props.axiom
            rules = _parse_rules(props.rules_str)
            angle = props.angle
            roll_angle = props.roll_angle if props.use_custom_roll else None
            iterations = props.iterations
            length = props.length
            skin = props.skin
            base_radius = props.base_radius
            tip_radius = props.tip_radius
            branch_decay = props.branch_decay
            randomize = props.randomize
            seed_val = props.seed if props.seed != 0 else None
            leaves = props.leaves
            leaf_size = props.leaf_size
            flowers = props.flowers
            flower_size = props.flower_size
            flower_petals = props.flower_petals
            flower_probability = props.flower_probability

        system_string = generate_lsystem(iterations, axiom, rules)

        if len(system_string) > 500_000:
            self.report({'WARNING'}, f"L-System string very long ({len(system_string)} chars) — may be slow")

        draw_lsystem_3d(
            system_string, length=length, angle=angle,
            roll_angle=roll_angle,
            skin=skin, base_radius=base_radius,
            tip_radius=tip_radius, branch_decay=branch_decay,
            randomize=randomize, seed=seed_val,
            leaves=leaves, leaf_size=leaf_size,
            flowers=flowers, flower_size=flower_size,
            flower_petals=flower_petals,
            flower_probability=flower_probability,
            clean_scene=props.clean_scene,
        )

        self.report({'INFO'}, f"L-System generated ({len(system_string)} symbols)")
        return {'FINISHED'}


class LSYSTEM_OT_load_preset(bpy.types.Operator):
    """Load preset values into custom fields for tweaking"""
    bl_idname = "lsystem.load_preset"
    bl_label = "Load into Custom"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.lsystem_props
        if props.preset not in _PRESETS:
            self.report({'WARNING'}, "Select a preset first")
            return {'CANCELLED'}

        p = _PRESETS[props.preset]
        props.axiom = p['axiom']
        props.rules_str = p['rules_str']
        props.angle = p['angle']
        props.use_custom_roll = p['use_custom_roll']
        props.roll_angle = p['roll_angle']
        props.iterations = p['iterations']
        props.length = p['length']
        props.skin = p['skin']
        props.base_radius = p['base_radius']
        props.tip_radius = p['tip_radius']
        props.branch_decay = p['branch_decay']
        props.randomize = p['randomize']
        props.seed = p['seed']
        props.leaves = p['leaves']
        props.leaf_size = p['leaf_size']
        props.flowers = p['flowers']
        props.flower_size = p['flower_size']
        props.flower_petals = p['flower_petals']
        props.flower_probability = p['flower_probability']
        props.preset = 'CUSTOM'

        self.report({'INFO'}, f"Loaded preset into custom fields — tweak and generate!")
        return {'FINISHED'}


class LSYSTEM_PT_main(bpy.types.Panel):
    bl_label = "L-System 3D"
    bl_idname = "LSYSTEM_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "L-System"

    def draw(self, context):
        layout = self.layout
        props = context.scene.lsystem_props

        box = layout.box()
        box.label(text="Preset", icon='PRESET')
        box.prop(props, "preset", text="")

        if props.preset != 'CUSTOM':
            box.operator("lsystem.load_preset", icon='IMPORT')

        if props.preset == 'CUSTOM':
            box = layout.box()
            box.label(text="L-System Rules", icon='FILE_TEXT')
            box.prop(props, "axiom")
            box.prop(props, "rules_str")
            box.prop(props, "iterations")

            box = layout.box()
            box.label(text="Geometry", icon='MESH_DATA')
            box.prop(props, "length")
            box.prop(props, "angle")
            box.prop(props, "use_custom_roll")
            if props.use_custom_roll:
                box.prop(props, "roll_angle")

            box = layout.box()
            box.label(text="Skin Modifier", icon='MOD_SKIN')
            box.prop(props, "skin")
            if props.skin:
                box.prop(props, "base_radius")
                box.prop(props, "tip_radius")
                box.prop(props, "branch_decay")

            box = layout.box()
            box.label(text="Randomize", icon='FORCE_TURBULENCE')
            box.prop(props, "randomize")
            box.prop(props, "seed")

            box = layout.box()
            box.label(text="Decoration", icon='OUTLINER_OB_MESH')
            box.prop(props, "leaves")
            if props.leaves:
                box.prop(props, "leaf_size")
            box.prop(props, "flowers")
            if props.flowers:
                box.prop(props, "flower_size")
                box.prop(props, "flower_petals")
                box.prop(props, "flower_probability")

        layout.separator()
        layout.prop(props, "clean_scene")
        layout.operator("lsystem.generate", icon='PLAY', text="Generate L-System")


_classes = (
    LSystemProperties,
    LSYSTEM_OT_generate,
    LSYSTEM_OT_load_preset,
    LSYSTEM_PT_main,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lsystem_props = bpy.props.PointerProperty(type=LSystemProperties)


def unregister():
    del bpy.types.Scene.lsystem_props
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
