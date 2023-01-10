import pygame

equation = input("Input equation: ")
print(equation)

screen_width = 800
screen_height = 800

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

font_size = 26
elem_width = 80
padding = 10
elem_height = 40

pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height))

viewport_x = 0
viewport_y = 0
viewport_scale = 0
left_mouse_pressed = False

height_padding = 50
left_elems_y = screen_height//2 - elem_height//2 + padding

rects_used = []
wires = []
logic_inputs = {}
objs = []


class element_types(enumerate):
    LOGICAL_AND = 1
    LOGICAL_OR = 2
    LOGICAL_NOT = 3


class logical_element():
    def __init__(self, x, y, type) -> None:
        self.init_x = x
        self.x = x
        self.init_y = y
        self.y = y
        path_to_file = ""
        if type == element_types.LOGICAL_AND:
            path_to_file = './and.svg'
        elif type == element_types.LOGICAL_OR:
            path_to_file = './or.svg'
        elif type == element_types.LOGICAL_NOT:
            path_to_file = './not.svg'
        self.obj = pygame.transform.scale(
            pygame.image.load(path_to_file), (elem_width, elem_height))


def check_brackets(equation):
    stack = []
    count = 0
    for symbol in equation:
        if symbol in ['[', '(', '{']:
            stack.append(symbol)
            count += 1
        if symbol in [']', ')', '}']:
            if count <= 0:
                return False
            elif (symbol == ']' and stack[-1] != '[') or (symbol == '}' and stack[-1] != '{') or (symbol == ')' and symbol[-1] != '('):
                return False
            else:
                stack.pop()
                count -= 1
    return count == 0


def wire_collide_vertical(line):
    for wire in wires:
        if wire[0][0] == line[0][0] and wire[1][0] == line[1][0]:
            if (wire[0][1] <= line[0][1] and wire[1][1] >= line[0][1]) or (line[0][1] <= wire[0][1] and line[1][1] >= wire[0][1]):
                return True
    return False


def wire_collide_horizontal(line):
    pass


def wire_constructor(x1, y1, x2, y2, signal):
    dx = x2-x1
    dy = y2-y1

    collide_h = False
    collide_v = False

    kink_dots = [[x1 + abs(x2-x1)*0.1, y1], [x2, y1 + abs(y2-y1)*0.9]]
    wire_new_y, wire_new_x = y1, x2

    if dx != 0:
        wire_rect = pygame.rect.Rect(x1, y1, abs(x2-x1), 5)
        for ur in rects_used:
            while wire_rect.colliderect(ur):
                collide_h = True
                wire_rect.y -= 2

        while True:
            wires_collide = False
            for wire in wires:
                if wire[0][1] == wire_rect.y:
                    wire_rect.y -= 2
                    wires_collide = True

            if not wires_collide:
                break

        wire_new_y = wire_rect.y

    if dy != 0:
        wire_rect = pygame.rect.Rect(x2, y1, 3, abs(y2-y1))
        for ur in rects_used:
            while wire_rect.colliderect(ur):
                collide_v = True
                wire_rect.x -= 1

        while True:
            wires_collide = False
            for wire in wires:
                if wire[0][0] == wire_rect.x:
                    wire_rect.x -= -2
                    wires_collide = True

            if not wires_collide:
                break

        wire_new_x = wire_rect.x

    if collide_h and collide_v:
        wires.append([[kink_dots[0][0], wire_new_y], [
            wire_new_x, wire_new_y], signal])
        wires.append([[x1, y1], [kink_dots[0][0], y1], signal])
        wires.append([[wire_new_x, wire_new_y], [
            wire_new_x, kink_dots[1][1]], signal])
        wires.append([[kink_dots[1][0], kink_dots[1][1]],
                      [kink_dots[1][0], y2], signal])
        wire_constructor(kink_dots[0][0], wire_new_y,
                         kink_dots[0][0], y1, signal)
        wire_constructor(
            wire_new_x, kink_dots[1][1], x2, kink_dots[1][1], signal)

    elif collide_h:
        wires.append([[kink_dots[0][0], wire_new_y], [
            wire_new_x, wire_new_y], signal])
        wires.append([[x1, y1], [kink_dots[0][0], y1], signal])
        wire_constructor(kink_dots[0][0], wire_new_y,
                         kink_dots[0][0], y1, signal)
        wire_constructor(x2, wire_new_y, x2, y2, signal)
    elif collide_v:
        wires.append([[wire_new_x, wire_new_y], [
            wire_new_x, kink_dots[1][1]], signal])
        wires.append([[kink_dots[1][0], kink_dots[1][1]],
                      [kink_dots[1][0], y2], signal])
        wire_constructor(
            wire_new_x, kink_dots[1][1], x2, kink_dots[1][1], signal)
    else:
        wires.append([[x1, y1], [x2, y1], signal])
        wires.append([[x2, y1], [x2, y2], signal])


def add_elem_to_arr(elem):
    elem_type, left, right, x, y = elem
    objs.append(logical_element(x, y, elem_type))

    if type(left) == list:
        add_elem_to_arr(left)

    if type(right) == list:
        add_elem_to_arr(right)


def get_string(object):
    if type(object) == str:
        return object
    sign = object[0]
    left = object[1]
    right = object[2]
    if type(left) == list:
        left = f"({get_string(left)})"
    if type(right) == list:
        right = f"({get_string(right)})"
    if sign == element_types.LOGICAL_OR:
        return f"{left}+{right}"
    elif sign == element_types.LOGICAL_AND:
        return f"{left}*{right}"
    return ""


def process_elems(tree):
    global left_elems_y, height_padding
    elem_type, left, right, x, y = tree
    lt, rt = type(left), type(right)

    if lt == list:
        process_elems(left)
    if rt == list:
        process_elems(right)

    equal = f"{get_string(left)}{'+' if elem_type == element_types.LOGICAL_OR else '*'}{get_string(right)}"

    if lt == list and rt == list:
        x = max(left[3], right[3]) + 200
        y = (left[4] + right[4])//2 - elem_height//2
        wire_constructor(left[3] + elem_width,
                         left[4] + elem_height//2, x, y+padding, equal)
        wire_constructor(right[3] + elem_width,
                         right[4] + elem_height//2, x, y+elem_height-padding, equal)

    elif lt == list:
        x = left[3] + 200
        y = left[4] + padding
        wire_constructor(left[3] + elem_width,
                         left[4] + elem_height//2, x, y+padding, equal)
        wire_constructor(logic_inputs[right][0],
                         logic_inputs[right][1] + font_size//2, x, y+elem_height-padding, equal)

    elif rt == list:
        x = right[3] + 200
        y = right[4] - padding
        wire_constructor(
            logic_inputs[left][0], logic_inputs[left][1] + font_size//2, x, y+padding, equal)
        wire_constructor(right[3] + elem_width,
                         right[4] + elem_height//2, x, y+elem_height-padding, equal)

    else:
        x = 100
        y = left_elems_y
        left_elems_y += height_padding
        wire_constructor(
            logic_inputs[left][0], logic_inputs[left][1] + font_size//3, x, y+padding, equal)
        wire_constructor(
            logic_inputs[right][0], logic_inputs[right][1] + font_size//3, x, y+elem_height-padding, equal)

    tree[3], tree[4] = x, y
    rects_used.append(pygame.rect.Rect(x, y, elem_width, elem_height))
    objs.append(logical_element(x, y, elem_type))


def parse_equation(equation):
    if not check_brackets(equation):
        print('Brackets error')
        quit(1)

    stack = []
    inputs = {}
    input_x = 10
    input_y = 0
    num_of_inputs = 0
    inputs_y_diff = 24

    n = len(equation)
    i = 0
    while i < n:
        s = equation[i]
        if s not in ['+', '*']:
            if s not in inputs.keys():
                logic_inputs[s] = [input_x, input_y]
                input_y += inputs_y_diff
                num_of_inputs += 1
            stack.append(s)
        elif s == "*":
            if len(stack) == 0 or i+1 >= n:
                print("Equation error!")
                quit(1)
            if equation[i+1] not in logic_inputs.keys():
                logic_inputs[equation[i+1]] = [input_x,
                                               input_y]
                input_y += inputs_y_diff
            stack.append([element_types.LOGICAL_AND,
                         stack.pop(), equation[i+1], 0, 0])
            i += 1
        elif s == "+":
            stack.append("+")
        i += 1
    print(stack)

    inputs_offset = (screen_height - (num_of_inputs - 1)*inputs_y_diff)/2

    for key in logic_inputs.keys():
        logic_inputs[key][1] += inputs_offset

    while len(stack) > 2:
        right = stack.pop()
        sign = stack.pop()
        left = stack.pop()

        if sign == '+':
            stack.append([element_types.LOGICAL_OR, left, right, 0, 0])

    process_elems(stack[0])


def main():
    global viewport_scale, viewport_x, viewport_y, left_mouse_pressed
    running = True

    prev_mouse_pos = pygame.mouse.get_pos()

    parse_equation(equation)

    font = pygame.font.SysFont('Roboto', font_size)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                left_mouse_pressed = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                left_mouse_pressed = False
            elif event.type == pygame.MOUSEMOTION and left_mouse_pressed:
                current_mouse_pos = pygame.mouse.get_pos()
                viewport_x += (current_mouse_pos[0] - prev_mouse_pos[0])
                viewport_y += (current_mouse_pos[1] - prev_mouse_pos[1])
                for l_obj in objs:
                    if type(l_obj) == logical_element:
                        l_obj.x = l_obj.init_x + viewport_x
                        l_obj.y = l_obj.init_y + viewport_y

        screen.fill(WHITE)

        for l_obj in objs:
            if type(l_obj) == logical_element:
                screen.blit(l_obj.obj, (l_obj.x, l_obj.y))

        for wire in wires:
            dot1 = [wire[0][0] + viewport_x, wire[0][1] + viewport_y]
            dot2 = [wire[1][0] + viewport_x, wire[1][1] + viewport_y]
            pygame.draw.line(screen, BLACK, dot1, dot2, 1)

        for logic_input in logic_inputs.keys():
            input_name = font.render(logic_input, True, BLACK)
            screen.blit(input_name, (logic_inputs[logic_input][0]-input_name.get_size()[
                0] + viewport_x, logic_inputs[logic_input][1] + viewport_y))

        prev_mouse_pos = pygame.mouse.get_pos()

        pygame.display.flip()


if __name__ == "__main__":
    main()
