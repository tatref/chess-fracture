
from io import StringIO

import os
from os import path
import sys
from pprint import pprint
import time
import re
import traceback

import bpy

try:
    import chess.pgn
except Exception as e:
    print('chess module missing (pip install python-chess?)')
    traceback.print_exc()
    sys.exit(1)


# square size in blender units
SQUARE_SIZE = 3.0

# center of gravity for the pieces
Z_MAP = {
    'king': 2.32912,
    'queen': 2.0401,
    'bishop': 1.7937,
    'knight': 1.,
    'rook': 1.46252,
    'pawn': 1.35288,
}


def chess_to_coordinates(row, col, z):
    x_map = {'a': 0., 'b': 1., 'c': 2., 'd': 3., 'e': 4., 'f': 5., 'g': 6., 'h': 7.}
    y_map = {'1': 0., '2': 1., '3': 2., '4': 3., '5': 4., '6': 5., '7': 6., '8': 7.}
    
    return (x_map[row] + 0.5) * SQUARE_SIZE, (y_map[col] + 0.5) * SQUARE_SIZE, z


def clean():
    for action in bpy.data.actions:
        if action.users == 0:
            bpy.data.actions.remove(action)
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def instantiate_piece(piece_name, player, board_location, z, name=None):
    col, row = board_location
    src_obj = bpy.context.scene.objects['template_' + piece_name]

    new_obj = src_obj.copy()
    new_obj.data = src_obj.data.copy()
    new_obj.animation_data_clear()

    if name:
        new_obj.name = name
    else:
        new_obj.name = piece_name + '.' + player + '.' + col + row
    
    bpy.context.scene.objects.link(new_obj)
    
    new_obj.location = chess_to_coordinates(col, row, z)
    new_obj.keyframe_insert(data_path='location')

    print('Instantiating ' + str(new_obj.name) + ' for ' + str(player) + ' at ' + str(new_obj.location))
    
    # physics
    bpy.context.scene.rigidbody_world.group.objects.link(new_obj)

    return new_obj


def initial_setup():
    clean()
    
    bpy.context.scene.layers[0] = True

    
    # remove stuff
    bpy.ops.object.select_all(action='DESELECT')
    for obj in filter(lambda x: not x.name.startswith('template_'), bpy.data.objects):
        obj.select = True
    bpy.ops.object.delete()

    
    bpy.context.scene.frame_set(1)
    bpy.context.scene.frame_end = 3000
    

    #bpy.ops.rigidbody.world_add()
    
    
    board_map = {}
    # PAWNS
    piece_name = 'pawn'
    for idx1, col in enumerate("abcdefgh"):
        for idx2, row in enumerate("27"):
            board_location = (col, row)
            if int(row) < 4:
                player = 'white'
            else:
                player = 'black'
            new_obj = instantiate_piece(piece_name, player, board_location, Z_MAP[piece_name])
            board_map[col + row] = new_obj

    # ROOKS
    piece_name = 'rook'
    for idx1, col in enumerate("ah"):
        for idx2, row in enumerate("18"):
            if int(row) < 4:
                player = 'white'
            else:
                player = 'black'
            board_location = (col, row)
            new_obj = instantiate_piece(piece_name, player, board_location, Z_MAP[piece_name])
            board_map[col + row] = new_obj
    # KNIGHTS
    piece_name = 'knight'
    for idx1, col in enumerate("bg"):
        for idx2, row in enumerate("18"):
            if int(row) < 4:
                player = 'white'
            else:
                player = 'black'
            board_location = (col, row)
            new_obj = instantiate_piece(piece_name, player, board_location, Z_MAP[piece_name])
            board_map[col + row] = new_obj
    # BISHOPS
    piece_name = 'bishop'
    for idx1, col in enumerate("cf"):
        for idx2, row in enumerate("18"):
            if int(row) < 4:
                player = 'white'
            else:
                player = 'black'
            board_location = (col, row)
            new_obj = instantiate_piece(piece_name, player, board_location, Z_MAP[piece_name])
            board_map[col + row] = new_obj
    # QUEENS
    piece_name = 'queen'
    for idx1, col in enumerate("d"):
        for idx2, row in enumerate("18"):
            if int(row) < 4:
                player = 'white'
            else:
                player = 'black'
            board_location = (col, row)
            new_obj = instantiate_piece(piece_name, player, board_location, Z_MAP[piece_name])
            board_map[col + row] = new_obj
    # KINGS
    piece_name = 'king'
    for idx1, col in enumerate("e"):
        for idx2, row in enumerate("18"):
            if int(row) < 4:
                player = 'white'
            else:
                player = 'black'
            board_location = (col, row)
            new_obj = instantiate_piece(piece_name, player, board_location, Z_MAP[piece_name])
            board_map[col + row] = new_obj
    
    # BOARD  
    bpy.ops.mesh.primitive_plane_add(view_align=False, enter_editmode=False, location=(0, 0, 0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
    bpy.context.selected_objects[0].name = 'ground'
    
    bpy.context.object.scale[1] = 4 * SQUARE_SIZE
    bpy.context.object.scale[0] = 4 * SQUARE_SIZE
    bpy.context.object.location[0] = 4 * SQUARE_SIZE
    bpy.context.object.location[1] = 4 * SQUARE_SIZE

    bpy.context.scene.rigidbody_world.group.objects.link(bpy.data.objects['ground'])

    # TODO: create checker texture
    checker_mat = bpy.data.materials.get('checker')
    bpy.data.objects['ground'].data.materials.append(checker_mat)

    bpy.context.scene.frame_set(2)
    bpy.context.scene.frame_set(3)
    bpy.context.scene.frame_set(1)
    
    bpy.data.objects['ground'].rigid_body.kinematic = True
    for piece in board_map.values():
        piece.rigid_body.kinematic = True


    return board_map
    


def load_pgn(pgn_path):
    print("Loading PGN " + str(pgn_path))
    try:
        with open(pgn_path) as pgn_file:
            game = chess.pgn.read_game(pgn_file)
    except Exception as e:
        print("Load PGN failed")
        traceback.print_exc()
        sys.exit(1)
    
    
    return game
    

def fracture(obj, n_fragments, current_frame):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select = True
    bpy.ops.object.add_fracture_cell_objects(source_limit=n_fragments)
    
    for o in filter(lambda x: x.name.startswith(obj.name + '_cell'), bpy.data.objects):
        bpy.context.scene.rigidbody_world.group.objects.link(o)

    bpy.context.scene.frame_set(1)
    bpy.context.scene.frame_set(2)
    bpy.context.scene.frame_set(current_frame)
    
    for o in filter(lambda x: x.name.startswith(obj.name + '_cell'), bpy.data.objects):
        print('enable rigid_body.kinematic for ' + str(o))
        o.rigid_body.kinematic = True
        o.keyframe_insert('rigid_body.kinematic')

    # disable old piece
    for o in bpy.data.objects:
        o.select = False
    obj.select = True

    # needed or obj.rigid_body is None
    bpy.context.scene.frame_set(0)
    bpy.context.scene.frame_set(1)
    bpy.context.scene.frame_set(2)
    bpy.context.scene.frame_set(0)

    obj.rigid_body.collision_groups[0] = True
    obj.keyframe_insert('rigid_body.collision_groups')
    obj.hide = False
    obj.keyframe_insert('hide')
    obj.hide_render = False
    obj.keyframe_insert('hide_render')
    
    bpy.context.scene.frame_set(current_frame - 1)
    obj.rigid_body.collision_groups[0] = False
    obj.keyframe_insert('rigid_body.collision_groups')
    obj.hide = True
    obj.keyframe_insert('hide')
    obj.hide_render = True
    obj.keyframe_insert('hide_render')
            
    # enable rigid body for cells
    bpy.context.scene.frame_set(current_frame - 1)
    for o in filter(lambda x: x.name.startswith(obj.name + '_cell'), bpy.data.objects):
        o.rigid_body.kinematic = True
        o.keyframe_insert('rigid_body.kinematic')
        o.rigid_body.collision_groups[0] = False
        o.keyframe_insert('rigid_body.collision_groups')
    bpy.context.scene.frame_set(current_frame)
    for o in filter(lambda x: x.name.startswith(obj.name + '_cell'), bpy.data.objects):
        o.rigid_body.kinematic = False
        o.keyframe_insert('rigid_body.kinematic')
        o.rigid_body.collision_groups[0] = True
        o.keyframe_insert('rigid_body.collision_groups')
    
    # hide/unhide
    bpy.context.scene.frame_set(0)
    for o in filter(lambda x: x.name.startswith(obj.name + '_cell'), bpy.data.objects):
        o.hide = True
        o.keyframe_insert('hide')
        o.hide_render = True
        o.keyframe_insert('hide_render')
    bpy.context.scene.frame_set(current_frame - 1)
    for o in filter(lambda x: x.name.startswith(obj.name + '_cell'), bpy.data.objects):
        o.hide = False
        o.keyframe_insert('hide')
        o.hide_render = False
        o.keyframe_insert('hide_render')


def play(board_map, game, frames_per_move, n_fragments):
    start_time = time.time()

    board = game.board()
    for move_number, move in enumerate(game.main_line()):
        from_square = move.uci()[0:2]
        to_square = move.uci()[2:4]
        
        is_capture = board.is_capture(move)
        is_castling = board.is_castling(move)
        is_kingside_castling = board.is_kingside_castling(move)
        is_queenside_castling = board.is_queenside_castling(move)
        is_en_passant = board.is_en_passant(move)
        promotion = move.promotion
    
        print('{}: {}, cap: {}, castl: {}, promot: {}'.format((move_number // 2) + 1, move, is_capture, is_castling, promotion))


        if is_castling:
            king = board_map[from_square]
            
            if to_square == 'g1':
                rook_from = 'h1'
                rook_dest = 'f1'
            elif to_square == 'c1':
                rook_from = 'a1'
                rook_dest = 'd1'
            elif to_square == 'g8':
                rook_from = 'h8'
                rook_dest = 'f8'
            elif to_square == 'c8':
                rook_from = 'a8'
                rook_dest = 'd8'
            rook = board_map[rook_from]
            
            # insert keyframes
            king.keyframe_insert(data_path='location')
            rook.keyframe_insert(data_path='location')
            
            bpy.context.scene.frame_set(bpy.context.scene.frame_current + frames_per_move)
            
            # move king
            king.location = chess_to_coordinates(to_square[0], to_square[1], king.location.z)
            king.keyframe_insert(data_path='location')
            
            # move rook
            rook.location = chess_to_coordinates(rook_dest[0], rook_dest[1], rook.location.z)
            rook.keyframe_insert(data_path='location')
            
            # update board
            board_map.pop(from_square)
            board_map.pop(rook_from)
            
            board_map[to_square] = king
            board_map[rook_dest] = rook
            
            # end if castling
        elif is_capture:
            # keyframe for previous position
            board_map[from_square].keyframe_insert(data_path='location')
            board_map[to_square].keyframe_insert('rigid_body.kinematic')
            
            bpy.context.scene.frame_set(bpy.context.scene.frame_current + 1)
            board_map[to_square].rigid_body.kinematic = False
            board_map[to_square].keyframe_insert('rigid_body.kinematic')
            bpy.context.scene.frame_set(bpy.context.scene.frame_current + -1)
            
            current_frame = bpy.context.scene.frame_current


            fracture(board_map[to_square], n_fragments, current_frame)
            
            
            # timestep
            bpy.context.scene.frame_set(current_frame + frames_per_move)
        
            # move piece
            board_map[from_square].location = chess_to_coordinates(to_square[0], to_square[1], board_map[from_square].location.z)
            board_map[from_square].keyframe_insert(data_path='location')
            
            
            
            
            # play the move on the board_map
            board_map[to_square] = board_map[from_square]
            board_map.pop(from_square)

        # end if capture
        else:
            # simple move
            # keyframe for previous position
            board_map[from_square].keyframe_insert(data_path='location')
            
            # timestep
            bpy.context.scene.frame_set(bpy.context.scene.frame_current + frames_per_move)
            
            # move piece
            board_map[from_square].location = chess_to_coordinates(to_square[0], to_square[1], board_map[from_square].location.z)
            board_map[from_square].keyframe_insert(data_path='location')
            
            # play the move on board
            board_map[to_square] = board_map[from_square]
            board_map.pop(from_square)

            # end simple move

        if promotion:
            TURN_COLOR_MAP = { True: 'white', False: 'black' }
            player = TURN_COLOR_MAP[board.turn]

            promoted_piece_name = chess.PIECE_NAMES[promotion]
            print('Promoted to: ' + str(promoted_piece_name))

            (col, row) = (to_square[0], to_square[1])
            z = Z_MAP[promoted_piece_name] - 10.
            promoted_piece = instantiate_piece(promoted_piece_name, player, (col, row), z, name='{}.{}.promoted.{}{}'.format(promoted_piece_name, player, col, row))
            promoted_piece.location[2] -= 10.

            print('promoted piece = ' + str(promoted_piece_name) + ', at ' + str((col, row)))
            pawn = board_map[col + row]
            print('promotion pawn = ' + str(pawn))
            
            # disable physics and display for promoted piece from #0 to #current_frame
            current_frame = bpy.context.scene.frame_current

            # otherwise promoted_piece.rigid_body == None
            bpy.context.scene.frame_set(2)
            bpy.context.scene.frame_set(3)
            bpy.context.scene.frame_set(1)
            bpy.context.scene.frame_set(current_frame - 1)

            promoted_piece.rigid_body.kinematic = True
            promoted_piece.keyframe_insert('rigid_body.kinematic')
            promoted_piece.rigid_body.collision_groups[0] = True
            promoted_piece.keyframe_insert('rigid_body.collision_groups')
            promoted_piece.hide = True
            promoted_piece.keyframe_insert('hide')
            promoted_piece.hide_render = True
            promoted_piece.keyframe_insert('hide_render')
            
            # promoted piece appears on #current_frame
            bpy.context.scene.frame_set(current_frame)
            promoted_piece.rigid_body.collision_groups[0] = True
            promoted_piece.keyframe_insert('rigid_body.collision_groups')
            promoted_piece.hide = False
            promoted_piece.keyframe_insert('hide')
            promoted_piece.hide_render = False
            promoted_piece.keyframe_insert('hide_render')

            # distroy pawn
            fracture(pawn, n_fragments, current_frame)

            # TODO
            # animate promoted piece?
            # update board_map
            print('TODO: promotion')
            break

        # update the board
        board.push(move)
        
        if 'CHESS_FRACTURE_TEST' in os.environ and move_number > 10:
            print('Early exit because CHESS_FRACTURE_TEST is defined')
            break
    # end for moves
    
    # assign materials
    white_mat = bpy.data.materials.get('white')
    black_mat = bpy.data.materials.get('black')
    
    whites_re = re.compile(r'.*white.*')
    blacks_re = re.compile(r'.*black.*')
    for obj in bpy.data.objects:
        if whites_re.match(obj.name):
            obj.data.materials.append(white_mat)
        elif blacks_re.match(obj.name):
            obj.data.materials.append(black_mat)

    # compute some stats
    end_time = time.time()
    duration = end_time - start_time
    print('Duration: ' + str(duration))
    # end def play


def get_env_or_default(name, default):
    if name in os.environ:
        return os.environ[name]
    else:
        return default


def main():
    frames_per_move = int(get_env_or_default('CHESS_FRACTURE_FRAMES_PER_MOVE', 20))
    print("CHESS_FRACTURE_FRAMES_PER_MOVE=" + str(frames_per_move))

    n_fragments = int(get_env_or_default('CHESS_FRACTURE_FRAGMENTS', 10))
    print("CHESS_FRACTURE_FRAGMENTS=" + str(n_fragments))

    pgn_path = get_env_or_default('CHESS_FRACTURE_PGN_PATH', '/work/input.pgn')
    game = load_pgn(pgn_path)

    variant = game.board().uci_variant
    if variant != 'chess':
        sys.stdout.write('Unsupported game type {}\n'.format(variant))
        sys.exit(1)

    board_map = initial_setup()
    print('Board setup done')

    try:
        play(board_map, game, frames_per_move, n_fragments)
        print('Simulation done')
    except Exception as e:
        print('Simulation failed')
        traceback.print_exc()
        sys.exit(1)

    try:
        if 'CHESS_FRACTURE_OUT_BLEND' in os.environ:
            save_file = os.environ['CHESS_FRACTURE_OUT_BLEND']
        
            bpy.ops.wm.save_as_mainfile(filepath=save_file)
        
            print('File saved as "{}"'.format(save_file))
        
            sys.exit(0)  # happy path
    except Exception as e:
        print('Save failed ' + str(e))
        traceback.print_exc()
        sys.exit(1)
    # end def main


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('main failed :' + str(e))
        traceback.print_exc()
        sys.exit(1)
