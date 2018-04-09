
from io import StringIO

import os
from os import path
import sys
from pprint import pprint
import time
import re

import bpy

import chess.pgn
import requests



SQUARE_SIZE = 3.0

if 'CHESS_FRACTURE_FRAMES_PER_MOVE' in os.environ:
    frames_per_move = os.environ['CHESS_FRACTURE_FRAMES_PER_MOVE']
else:
    frames_per_move = 20

if 'CHESS_FRACTURE_FRAGMENTS' in os.environ:
    n_fragments = os.environ['CHESS_FRACTURE_FRAGMENTS']
else:
    n_fragments = 10



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

def initial_setup():
    clean()
    
    bpy.context.scene.layers[0] = True

    
    # remove stuff
    bpy.ops.object.select_all(action='DESELECT')
    for obj in filter(lambda x: not x.name.startswith('template_'), bpy.data.objects):
        obj.select = True
    bpy.ops.object.delete()

    
    bpy.context.scene.frame_set(1)
    bpy.context.scene.frame_end = 2000
    

    #bpy.ops.rigidbody.world_add()
    
    
    board_map = {}
    # PAWNS
    z = 1.35288
    for idx1, col in enumerate("abcdefgh"):
        for idx2, row in enumerate("27"):
            src_obj = bpy.context.scene.objects['template_pawn']

            new_obj = src_obj.copy()
            new_obj.data = src_obj.data.copy()
            new_obj.animation_data_clear()
            new_obj.name = 'pawn.' + col + row
            
            bpy.context.scene.objects.link(new_obj)
            
            board_map[col + row] = new_obj
            new_obj.location = chess_to_coordinates(col, row, z)
            new_obj.keyframe_insert(data_path='location')
            
            # physics
            bpy.context.scene.rigidbody_world.group.objects.link(new_obj)

    # ROOKS
    z = 1.46252
    for idx1, col in enumerate("ah"):
        for idx2, row in enumerate("18"):
            src_obj = bpy.context.scene.objects['template_rook']

            new_obj = src_obj.copy()
            new_obj.data = src_obj.data.copy()
            new_obj.animation_data_clear()
            new_obj.name = 'rook.' + col + row
            
            bpy.context.scene.objects.link(new_obj)
            
            board_map[col + row] = new_obj
            new_obj.location = chess_to_coordinates(col, row, z)
            new_obj.keyframe_insert(data_path='location')
            bpy.context.scene.rigidbody_world.group.objects.link(new_obj)
    # KNIGHTS
    z = 1.
    for idx1, col in enumerate("bg"):
        for idx2, row in enumerate("18"):
            src_obj = bpy.context.scene.objects['template_knight']

            new_obj = src_obj.copy()
            new_obj.data = src_obj.data.copy()
            new_obj.animation_data_clear()
            new_obj.name = 'knight.' + col + row
            
            bpy.context.scene.objects.link(new_obj)
            
            board_map[col + row] = new_obj
            new_obj.location = chess_to_coordinates(col, row, z)
            new_obj.keyframe_insert(data_path='location')
            bpy.context.scene.rigidbody_world.group.objects.link(new_obj)
    # BISHOPS
    z = 1.7937
    for idx1, col in enumerate("cf"):
        for idx2, row in enumerate("18"):
            src_obj = bpy.context.scene.objects['template_bishop']

            new_obj = src_obj.copy()
            new_obj.data = src_obj.data.copy()
            new_obj.animation_data_clear()
            new_obj.name = 'bishop.' + col + row
            
            bpy.context.scene.objects.link(new_obj)
            
            board_map[col + row] = new_obj
            new_obj.location = chess_to_coordinates(col, row, z)
            new_obj.keyframe_insert(data_path='location')
            bpy.context.scene.rigidbody_world.group.objects.link(new_obj)
    # QUEENS
    z = 0.5
    for idx1, col in enumerate("d"):
        for idx2, row in enumerate("18"):
            src_obj = bpy.context.scene.objects['template_queen']

            new_obj = src_obj.copy()
            new_obj.data = src_obj.data.copy()
            new_obj.animation_data_clear()
            new_obj.name = 'queen.' + col + row
            
            bpy.context.scene.objects.link(new_obj)
            
            board_map[col + row] = new_obj
            new_obj.location = chess_to_coordinates(col, row, z)
            new_obj.keyframe_insert(data_path='location')
            bpy.context.scene.rigidbody_world.group.objects.link(new_obj)
    # KINGS
    z = 2.32912
    for idx1, col in enumerate("e"):
        for idx2, row in enumerate("18"):
            src_obj = bpy.context.scene.objects['template_king']

            new_obj = src_obj.copy()
            new_obj.data = src_obj.data.copy()
            new_obj.animation_data_clear()
            new_obj.name = 'king.' + col + row
            
            bpy.context.scene.objects.link(new_obj)
            
            board_map[col + row] = new_obj
            new_obj.location = chess_to_coordinates(col, row, z)
            new_obj.keyframe_insert(data_path='location')
            bpy.context.scene.rigidbody_world.group.objects.link(new_obj)
    
    # BOARD  
    bpy.ops.mesh.primitive_plane_add(view_align=False, enter_editmode=False, location=(0, 0, 0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
    bpy.context.selected_objects[0].name = 'ground'
    
    bpy.context.object.scale[1] = 4 * SQUARE_SIZE
    bpy.context.object.scale[0] = 4 * SQUARE_SIZE
    bpy.context.object.location[0] = 4 * SQUARE_SIZE
    bpy.context.object.location[1] = 4 * SQUARE_SIZE

    bpy.context.scene.rigidbody_world.group.objects.link(bpy.data.objects['ground'])

    bpy.data.materials.new(name='checker_texture')
    bpy.data.materials['checker_texture'].use_nodes = True
    # TODO: create checker texture

    bpy.context.scene.frame_set(2)
    bpy.context.scene.frame_set(3)
    bpy.context.scene.frame_set(1)
    
    bpy.data.objects['ground'].rigid_body.kinematic = True
    for piece in board_map.values():
        piece.rigid_body.kinematic = True


    return board_map
    


def load_pgn(pgn_path):
    with open(pgn_path) as pgn_file:
        game = chess.pgn.read_game(pgn_file)
    
    
    return game
    

def play(board_map, game):
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
    
        print('{}: {}, cap: {}, castl: {}'.format((move_number // 2) + 1, move, is_capture, is_castling))


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
            
            
        elif is_capture:
            # keyframe for previous position
            board_map[from_square].keyframe_insert(data_path='location')
            board_map[to_square].keyframe_insert('rigid_body.kinematic')
            
            bpy.context.scene.frame_set(bpy.context.scene.frame_current + 1)
            board_map[to_square].rigid_body.kinematic = False
            board_map[to_square].keyframe_insert('rigid_body.kinematic')
            bpy.context.scene.frame_set(bpy.context.scene.frame_current + -1)
            
            bpy.ops.object.select_all(action='DESELECT')
            board_map[to_square].select = True
            bpy.ops.object.add_fracture_cell_objects(source_limit=n_fragments)
            
            for obj in filter(lambda x: x.name.startswith(board_map[to_square].name + '_cell'), bpy.data.objects):
                bpy.context.scene.rigidbody_world.group.objects.link(obj)

            this_frame = bpy.context.scene.frame_current
            bpy.context.scene.frame_set(1)
            bpy.context.scene.frame_set(2)
            bpy.context.scene.frame_set(this_frame)
            
            for obj in filter(lambda x: x.name.startswith(board_map[to_square].name + '_cell'), bpy.data.objects):
                obj.rigid_body.kinematic = True
                obj.keyframe_insert('rigid_body.kinematic')

            # disable old piece
            for obj in bpy.data.objects:
                obj.select = False
            board_map[to_square].select = True
            bpy.context.scene.frame_set(0)
            board_map[to_square].rigid_body.collision_groups[0] = True
            board_map[to_square].keyframe_insert('rigid_body.collision_groups')
            board_map[to_square].hide = False
            board_map[to_square].keyframe_insert('hide')
            board_map[to_square].hide_render = False
            board_map[to_square].keyframe_insert('hide_render')
            
            bpy.context.scene.frame_set(this_frame - 1)
            board_map[to_square].rigid_body.collision_groups[0] = False
            board_map[to_square].keyframe_insert('rigid_body.collision_groups')
            board_map[to_square].hide = True
            board_map[to_square].keyframe_insert('hide')
            board_map[to_square].hide_render = True
            board_map[to_square].keyframe_insert('hide_render')
            
            
            
            # enable rigid body for cells
            bpy.context.scene.frame_set(this_frame - 1)
            for obj in filter(lambda x: x.name.startswith(board_map[to_square].name + '_cell'), bpy.data.objects):
                obj.rigid_body.kinematic = True
                obj.keyframe_insert('rigid_body.kinematic')
                obj.rigid_body.collision_groups[0] = False
                obj.keyframe_insert('rigid_body.collision_groups')
                
            bpy.context.scene.frame_set(this_frame)
            for obj in filter(lambda x: x.name.startswith(board_map[to_square].name + '_cell'), bpy.data.objects):
                obj.rigid_body.kinematic = False
                obj.keyframe_insert('rigid_body.kinematic')
                obj.rigid_body.collision_groups[0] = True
                obj.keyframe_insert('rigid_body.collision_groups')
            
            bpy.context.scene.frame_set(0)
            for obj in filter(lambda x: x.name.startswith(board_map[to_square].name + '_cell'), bpy.data.objects):
                obj.hide = True
                obj.keyframe_insert('hide')
                obj.hide_render = True
                obj.keyframe_insert('hide_render')
            bpy.context.scene.frame_set(this_frame - 1)
            for obj in filter(lambda x: x.name.startswith(board_map[to_square].name + '_cell'), bpy.data.objects):
                obj.hide = False
                obj.keyframe_insert('hide')
                obj.hide_render = False
                obj.keyframe_insert('hide_render')
            
            
            
            # timestep
            bpy.context.scene.frame_set(this_frame + frames_per_move)
        
            # move piece
            board_map[from_square].location = chess_to_coordinates(to_square[0], to_square[1], board_map[from_square].location.z)
            board_map[from_square].keyframe_insert(data_path='location')
            
            
            
            
            # actually play the move
            board_map[to_square] = board_map[from_square]
            board_map.pop(from_square)

        else:
            # simple move
            # keyframe for previous position
            board_map[from_square].keyframe_insert(data_path='location')
            
            # timestep
            bpy.context.scene.frame_set(bpy.context.scene.frame_current + frames_per_move)
            
            # move piece
            board_map[from_square].location = chess_to_coordinates(to_square[0], to_square[1], board_map[from_square].location.z)
            board_map[from_square].keyframe_insert(data_path='location')
            
            # actually play the move
            board_map[to_square] = board_map[from_square]
            board_map.pop(from_square)

        # update the board
        board.push(move)
        
        if 'CHESS_FRACTURE_TEST' in os.environ:
            break
    # end for moves
    
    # assign materials
    white_mat = bpy.data.materials.get('white')
    black_mat = bpy.data.materials.get('black')
    
    whites_re = re.compile(r'[a-z]+\.[a-h][12].*')
    blacks_re = re.compile(r'[a-z]+\.[a-h][78].*')
    for obj in bpy.data.objects:
        if whites_re.match(obj.name):
            obj.data.materials.append(white_mat)
        elif blacks_re.match(obj.name):
            obj.data.materials.append(black_mat)

    # compute some stats
    end_time = time.time()
    duration = end_time - start_time
    print('Duration: ' + str(duration))



if 'CHESS_FRACTURE_PGN_PATH' in os.environ:
    game = load_pgn(os.environ['CHESS_FRACTURE_PGN_PATH'])
else:
    game = load_pgn('/work/input.pgn')


board_map = initial_setup()
print('Board setup done')

try:
    play(board_map, game)
    print('Simulation done')
except Exception as e:
    print('Simulation failed')
    print(str(e))
    sys.exit(1)


if 'PGN_NAME' in os.environ:
    save_file = path.join('/output', os.environ['PGN_NAME'])

    bpy.ops.wm.save_as_mainfile(filepath=save_file)

    print('File saved as "{}"'.format(save_file))

    sys.exit(0)
