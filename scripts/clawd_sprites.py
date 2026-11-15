"""Render Clawd sprite frames (transparent PNG) for the usage widget.

Usage:
  blender --background --factory-startup --python clawd_sprites.py -- <state|all> [preview]

States (each is a seamless loop):
  idle    24 frames  gentle bob, one blink
  typing  16 frames  laptop open, arms tapping
  tired   32 frames  squashed, eyes nearly shut, slow breathing
Output: ../sprites/<state>/f000.png ...
"""
import bpy, bmesh, math, os, sys

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['all']
STATES = {'idle': 24, 'typing': 16, 'tired': 32}
WANT = list(STATES) if ARGS[0] == 'all' else [ARGS[0]]
PREVIEW = 'preview' in ARGS
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sprites')
U = 0.1
SIZE = 256
D = math.radians


def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c) + (1.0,)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    def material(name, hexcol, rough=0.5, coat=0.0, emit=None, emit_strength=0.0):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        p = m.node_tree.nodes['Principled BSDF']
        p.inputs['Base Color'].default_value = srgb(hexcol)
        p.inputs['Roughness'].default_value = rough
        if coat and 'Coat Weight' in p.inputs:
            p.inputs['Coat Weight'].default_value = coat
        if emit:
            p.inputs['Emission Color'].default_value = srgb(emit)
            p.inputs['Emission Strength'].default_value = emit_strength
        return m

    def box(name, x0, x1, y0, y1, z0, z1, mat, parent=None, loc=(0, 0, 0), bevel=0.012):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x = x0 + (v.co.x + 0.5) * (x1 - x0)
            v.co.y = y0 + (v.co.y + 0.5) * (y1 - y0)
            v.co.z = z0 + (v.co.z + 0.5) * (z1 - z0)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        scene.collection.objects.link(o)
        o.location = loc
        if parent:
            o.parent = parent
        if bevel:
            b = o.modifiers.new('Bevel', 'BEVEL')
            b.width = bevel
            b.segments = 4
        me.materials.append(mat)
        return o

    def empty(name, loc=(0, 0, 0), parent=None):
        e = bpy.data.objects.new(name, None)
        e.location = loc
        if parent:
            e.parent = parent
        scene.collection.objects.link(e)
        return e

    orange = material('Clawd Orange', '#D77757', rough=0.38, coat=0.25)
    black = material('Eye Black', '#0b0b0d', rough=0.15)
    alu = material('Laptop Shell', '#3a3d44', rough=0.35)
    keys_m = material('Keyboard', '#1c1d21', rough=0.6)
    screen_m = material('Screen', '#0e1626', rough=0.2, emit='#9fd0ff', emit_strength=3.0)

    r = {}
    r['rig'] = rig = empty('Rig')
    r['body'] = body_root = empty('BodyRoot', parent=rig)
    X = lambda c: (c - 9) * U
    box('Body', X(3), X(15), -0.3, 0.3, 0.2, 1.0, orange, parent=body_root)
    for i, c in enumerate((4, 6, 11, 13)):
        box(f'Leg {i + 1}', X(c), X(c + 1), -0.12, 0.12, 0.0, 0.22, orange, parent=rig)
    r['eyes'] = []
    for name, c in (('Eye L', 5), ('Eye R', 12)):
        cx = X(c) + 0.05
        r['eyes'].append(box(name, -0.05, 0.05, -0.04, 0.0, -0.1, 0.1, black,
                             parent=body_root, loc=(cx, -0.3, 0.7), bevel=0.004))
    r['shL'] = empty('Shoulder L', loc=(X(3), 0, 0.5), parent=body_root)
    r['shR'] = empty('Shoulder R', loc=(X(15), 0, 0.5), parent=body_root)
    r['armL'] = box('Arm L', -0.2, 0.0, -0.15, 0.15, -0.1, 0.1, orange, parent=r['shL'])
    r['armR'] = box('Arm R', 0.0, 0.2, -0.15, 0.15, -0.1, 0.1, orange, parent=r['shR'])

    r['lap'] = lap = empty('Laptop', loc=(0, -0.6, 0), parent=rig)
    box('Laptop Base', -0.46, 0.46, -0.26, 0.26, 0.0, 0.03, alu, parent=lap, bevel=0.008)
    box('Keyboard', -0.4, 0.4, -0.02, 0.2, 0.03, 0.034, keys_m, parent=lap, bevel=0.0)
    hinge = empty('Hinge', loc=(0, -0.26, 0.03), parent=lap)
    box('Lid', -0.46, 0.46, 0.0, 0.5, -0.015, 0.0, alu, parent=hinge, bevel=0.008)
    box('Screen', -0.41, 0.41, 0.04, 0.46, -0.019, -0.015, screen_m, parent=hinge, bevel=0.0)
    hinge.rotation_euler = (D(105), 0, 0)

    def area(name, loc, rot, energy, size, color=(1, 1, 1)):
        d = bpy.data.lights.new(name, 'AREA')
        d.energy, d.size, d.color = energy, size, color
        o = bpy.data.objects.new(name, d)
        o.location = loc
        o.rotation_euler = [D(v) for v in rot]
        scene.collection.objects.link(o)

    area('Key', (-2.2, -2.4, 2.6), (55, 0, -40), 190, 1.4, (1.0, 0.96, 0.9))
    area('Fill', (2.6, -2.0, 1.2), (70, 0, 50), 90, 3.0, (0.9, 0.94, 1.0))
    area('Rim', (0.8, 2.0, 2.4), (-50, 0, 160), 170, 1.2)
    world = bpy.data.worlds.new('World')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = srgb('#EFE6D8')
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35
    scene.world = world

    target = empty('Target', loc=(0, -0.2, 0.48))
    cam_d = bpy.data.cameras.new('Camera')
    cam_d.lens = 70
    cam = bpy.data.objects.new('Camera', cam_d)
    cam.location = (1.4, -4.2, 1.7)
    scene.collection.objects.link(cam)
    t = cam.constraints.new('TRACK_TO')
    t.target, t.track_axis, t.up_axis = target, 'TRACK_NEGATIVE_Z', 'UP_Y'
    scene.camera = cam

    scene.render.engine = 'BLENDER_EEVEE'
    try:
        scene.eevee.taa_render_samples = 48
    except AttributeError:
        pass
    scene.view_settings.view_transform = 'Standard'
    scene.render.film_transparent = True
    scene.render.resolution_x = scene.render.resolution_y = SIZE
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    return scene, r


def arms(r, tiltL, tiltR, swing, stretch):
    r['shL'].rotation_euler = (0, D(-tiltL), D(swing))
    r['shR'].rotation_euler = (0, D(tiltR), D(-swing))
    r['armL'].scale = (stretch, 1, 1)
    r['armR'].scale = (stretch, 1, 1)


def eyes(r, sz):
    for e in r['eyes']:
        e.scale = (1, 1, sz)


def pose(state, r, i, n):
    ph = i / n * 2 * math.pi
    body = r['body']
    r['rig'].rotation_euler = (0, 0, D(-20) if state == 'typing' else 0)
    if state == 'idle':
        r['lap'].scale = (0, 0, 0)
        arms(r, 0, 0, 0, 1.0)
        body.location = (0, 0, 0.008 * (1 - math.cos(ph)) / 2)
        body.scale = (1, 1, 1)
        # blink centred on frame 14 of 24
        d = abs(i - 14)
        eyes(r, {0: 0.12, 1: 0.5}.get(d, 1.0))
    elif state == 'typing':
        r['lap'].scale = (1, 1, 1)
        tap = (i // 2) % 2 == 0          # alternate hands every 2 frames
        arms(r, 60 if tap else 46, 46 if tap else 60, 74, 2.1)
        body.location = (0, 0, 0.012 if (i // 4) % 2 else 0.0)
        body.scale = (1, 1, 1)
        eyes(r, 1.0)
    elif state == 'tired':
        r['lap'].scale = (0, 0, 0)
        arms(r, -25, -25, 0, 1.0)        # arms drooping
        breathe = (1 - math.cos(ph)) / 2
        body.scale = (1.0 + 0.03 * breathe, 1, 0.86 + 0.03 * breathe)
        body.location = (0, 0, 0)
        eyes(r, 0.15)


def main():
    scene, r = build()
    for state in WANT:
        n = STATES[state]
        out = os.path.join(OUT_DIR, state)
        os.makedirs(out, exist_ok=True)
        frames = [0, n // 2] if PREVIEW else range(n)
        for i in frames:
            pose(state, r, i, n)
            bpy.context.view_layer.update()
            scene.render.filepath = os.path.join(out, f'f{i:03d}.png')
            bpy.ops.render.render(write_still=True)
        print(f'{state}: {len(list(frames))} frames')
    print('SPRITES DONE')


if __name__ == '__main__':      # importable by the v2 scripts
    main()
