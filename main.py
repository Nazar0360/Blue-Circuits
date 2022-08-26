import pathlib as pl
import numpy as np
import copy as c
from Packages.ImageOperations import *


class Game:
    def get_mouse_position(self):
        pos = np.array(pg.mouse.get_pos())
        pos //= self.textures_size
        pos = np.floor(pos)
        return pos, pos * self.textures_size

    def __init__(self, fps: int = 30, visible_area_shape=(16, 16), textures_size=(32, 32)):
        self.__textures_size = np.array(textures_size)
        self.__visible_area_shape = np.array(visible_area_shape)
        self.__screen = Game.Screen(self, self.__textures_size * self.__visible_area_shape)
        self.__clock = pg.time.Clock()
        self.__fps = fps

        Game.Screen.load_textures('Default', textures_size)

    def update(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                exit()
            if pg.mouse.get_pressed(3)[0]:
                if Game.Object.get_object_in_pos(pos := self.get_mouse_position()[0]) is None:
                    Game.Wire(self, pos)
                elif not isinstance(obj := Game.Object.get_object_in_pos(pos), Game.Wire):
                    obj.rotate()
            if pg.mouse.get_pressed(3)[2]:
                Game.Object.delete_objects_in_pos(self.get_mouse_position()[0])
        self.__screen.update()
        self.__clock.tick(self.__fps)

    @property
    def textures_size(self):
        return self.__textures_size

    @property
    def visible_area_shape(self):
        return self.__visible_area_shape

    class Screen:
        textures = {}

        @staticmethod
        def grayscale_texture(texture, alpha: float = 1):
            return overlay(texture, grayscale(texture), alpha)

        @staticmethod
        def get_texture(name, texture_pack_name, size):
            return pg.transform.scale(
                pg.image.load(pl.Path(__file__).parent / 'Texture Packs' / texture_pack_name / name), size)

        @staticmethod
        def load_textures(texture_pack_name, size):
            from os import walk

            filenames = next(walk(pl.Path(__file__).parent / 'Texture Packs' / texture_pack_name),
                             (None, None, []))[2]

            for name in filenames:
                if name[-4:] in ['.png', '.jpg']:
                    Game.Screen.textures.update({name: Game.Screen.get_texture(name, texture_pack_name, size)})

        def highlight_mouse_position(self):
            s = pg.Surface(self.textures_size)
            s.set_alpha(128)
            s.fill((255, 255, 255))
            self.__screen.blit(s, self.__game.get_mouse_position()[1])

        def __init__(self, game: 'Game', size):
            self.__screen = pg.display.set_mode(size)
            self.__game = game
            self.__empty_space_texture = pg.transform.scale(
                pg.image.load(pl.Path(__file__).parent / 'Texture Packs' / 'Default' /
                              'empty_space.png'), self.__game.textures_size)

        def update(self):
            self.__screen.fill((0, 0, 0))

            for y in range(self.visible_area_shape[1]):
                for x in range(self.visible_area_shape[0]):
                    self.__screen.blit(self.__empty_space_texture, (x, y) * self.textures_size)

            for obj in Game.Object.objects.values():
                obj.draw(self.__screen)

            self.highlight_mouse_position()

            pg.display.flip()

        @property
        def textures_size(self):
            return self.__game.textures_size

        @property
        def visible_area_shape(self):
            return self.__game.visible_area_shape

    class Object:
        objects = {}

        @staticmethod
        def get_object_in_pos(pos) -> 'Game.Object':
            pos = tuple(pos)
            return Game.Object.objects.get(pos, None)

        @staticmethod
        def get_neighbors(pos):
            to_return = []
            for local_pos in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                to_return.append((Game.Object.get_object_in_pos(pos + np.array(local_pos)), local_pos))
            return to_return

        @staticmethod
        def update_neighbors(pos):
            for neighbor, _ in Game.Object.get_neighbors(pos):
                if neighbor is None:
                    continue
                neighbor.update()

        @staticmethod
        def delete_objects_in_pos(pos):
            pos = tuple(pos)
            objects = Game.Object.get_object_in_pos(pos)

            if objects is None:
                return

            Game.Object.objects.pop(pos)
            Game.Object.update_neighbors(pos)

        def __init__(self, game: 'Game', pos, texture, rotation=0, inputs=None, outputs=None):
            self._game = game
            self._pos = tuple(pos)
            self._texture = texture
            self._rotation = rotation
            self._texture = pg.transform.scale(self._texture, self.textures_size)
            self._input_texture = Game.Screen.textures['input.png']
            self._output_texture = Game.Screen.textures['output.png']
            self._i_o_texture = Game.Screen.textures['i_o.png']

            standard = {(0, -1): {'exists': False, 'id': 0, 'power': 0},
                        (0, 1): {'exists': False, 'id': 1, 'power': 0},
                        (-1, 0): {'exists': False, 'id': 2, 'power': 0},
                        (1, 0): {'exists': False, 'id': 3, 'power': 0}}

            self._inputs = c.deepcopy(standard)
            if inputs is not None:
                for key in standard:
                    self._inputs[key]['exists'] = inputs.get(key, False)

            self._outputs = c.deepcopy(standard)
            if outputs is not None:
                for key in standard:
                    self._outputs[key]['exists'] = outputs.get(key, False)

            self.rotate(self._rotation)
            Game.Object.objects.update({self._pos: self})

        def draw(self, screen: pg.Surface):
            screen.blit(pg.transform.rotate(self._texture, self._rotation * -90), self._pos * self.textures_size)
            rotation = {(0, -1): 90, (0, 1): 270, (-1, 0): 180, (1, 0): 0}

            for _input, _output in zip(self._inputs.items(), self._outputs.items()):
                _input: list
                _output: list

                if _input[1]['exists'] and _output[1]['exists']:
                    screen.blit(pg.transform.rotate(self._i_o_texture, rotation[_input[0]]),
                                self._pos * self.textures_size)
                elif _input[1]['exists']:
                    screen.blit(pg.transform.rotate(self._input_texture, rotation[_input[0]]),
                                self._pos * self.textures_size)
                elif _output[1]['exists']:
                    screen.blit(pg.transform.rotate(self._output_texture, rotation[_output[0]]),
                                self._pos * self.textures_size)

        def update(self):
            self.send_power()

        def take_power(self, _input, power):
            _input = tuple(_input)
            if _input not in self._inputs:
                return

            self._inputs[_input]['power'] = power

        def send_power(self):
            for _output in self._outputs.items():
                power = _output[1]['power']
                obj = Game.Object.get_object_in_pos(self._pos + _output[0])
                if obj is None:
                    continue
                obj.take_power(np.array(_output[0]) * -1, power)

        def rotate(self, times=1):
            times = -int(times) % 4
            self._rotation += times

            for _ in range(times):
                self._inputs[(0, -1)], self._inputs[(0, 1)], self._inputs[(-1, 0)], self._inputs[(1, 0)] = \
                    self._inputs[(1, 0)], self._inputs[(-1, 0)], self._inputs[(0, -1)], self._inputs[(0, 1)]

                self._outputs[(0, -1)], self._outputs[(0, 1)], self._outputs[(-1, 0)], self._outputs[(1, 0)] = \
                    self._outputs[(1, 0)], self._outputs[(-1, 0)], self._outputs[(0, -1)], self._outputs[(0, 1)]

            self.update_neighbors(self.pos)

        @property
        def textures_size(self):
            return self._game.textures_size

        @property
        def texture(self):
            return self._texture

        @texture.setter
        def texture(self, texture):
            self._texture = texture

        @property
        def pos(self):
            return self._pos

        @property
        def inputs(self):
            return self._inputs

        @property
        def outputs(self):
            return self._outputs

    class Wire(Object):
        max_power = 15
        min_power = 0

        def __init__(self, game, pos):
            super().__init__(game, pos, Game.Screen.textures['wire_c.png'])
            self._inputs = self._outputs
            self._i_o_texture = Game.Screen.textures['wire.png']
            self.update()

            Game.Object.update_neighbors(self.pos)

        def connect(self, obj):
            if obj is None:
                return False
            obj: Game.Object

            difference = tuple(np.array(obj.pos) - self.pos)

            if difference not in self._inputs:
                return False

            elif obj._inputs[tuple(np.array(difference) * -1)]['exists'] \
                    or obj._outputs[tuple(np.array(difference) * -1)]['exists'] \
                    or isinstance(obj, Game.Wire):
                self._inputs[difference]['exists'] = True
                return True

            return False

        def disconnect(self, local_pos):
            if local_pos not in self._inputs:
                return False
            self._inputs[local_pos]['exists'] = False

            return True

        def update(self):
            for neighbor, local_pos in self.get_neighbors(self.pos):
                neighbor: Game.Object
                if not self.connect(neighbor):
                    self.disconnect(local_pos)

            neighbor_amount = 0
            for _ in self._inputs.values():
                if _['exists']:
                    neighbor_amount += 1
            self.texture = Game.Screen.textures['wire_c.png']
            super().update()

        def draw(self, screen):
            super().draw(screen)

    class Wall(Object):
        def __init__(self, game, pos):
            super().__init__(game, pos, Game.Screen.textures['wall.png'])

    class PowerBlock(Object):
        def __init__(self, game, pos):
            super().__init__(game, pos, Game.Screen.textures['power_block.png'], outputs={(0, -1): True, (0, 1): True,
                                                                                          (-1, 0): True, (1, 0): True})


def main():
    game = Game()
    Game.Object(game, (1, 1), Game.Screen.textures['wire_c.png'], 1,
                inputs={(0, -1): True},
                outputs={(0, 1): True})

    Game.PowerBlock(game, (7, 7))

    while True:
        game.update()


if __name__ == '__main__':
    main()
