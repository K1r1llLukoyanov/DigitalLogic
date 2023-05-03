import pygame
import time
from sys import platform

expression = ""

screen_width = 1000
screen_height = 1000

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

elem_width = 80
elem_height = 60
padding = elem_height//4

screen = None

zoom_scale = 1

viewport_x = 0
viewport_y = 0
viewport_scale = 0
left_mouse_pressed = False

height_padding = 50
left_elems_y = screen_height//2 - elem_height//2 + padding

elems = []
wires = []

x_offset = 70 + elem_width
y_offset = 30


class element_types(enumerate):
    LOGICAL_AND = 1
    LOGICAL_OR = 2
    LOGICAL_NOT = 3
    LOGICAL_XOR = 4


class SYMBOL_TYPES(enumerate):
    ARITHMETIC = 0
    NOT = 1
    VARIABLE = 2
    OPEN_BRACKET = 3
    CLOSE_BRACKET = 4


class logical_element():
    def __init__(self, x, y, type) -> None:
        self.init_x = x
        self.x = x
        self.init_y = y
        self.y = y
        self.path_to_file = ""
        if type == element_types.LOGICAL_AND:
            self.path_to_file = './and.svg'
        elif type == element_types.LOGICAL_OR:
            self.path_to_file = './or.svg'
        elif type == element_types.LOGICAL_NOT:
            self.path_to_file = './not.svg'
        elif type == element_types.LOGICAL_XOR:
            self.path_to_file = './xor.svg'
        self.obj = pygame.transform.scale(
            pygame.image.load(self.path_to_file), (elem_width, elem_height))


class TreeNode(object):
    def __init__(self, data, left=None, right=None) -> None:
        self.data = data
        self.left = left
        self.right = right


class SignError():
    def __init__(self, message: str) -> None:
        self.message = message

    def what(self):
        return self.message


def check_brackets(expression: str) -> bool:
    """
        Check that all brackets from correct pairs using stack
    """
    stack = []
    count = 0
    for symbol in expression:
        if symbol in ['[', '(', '{']:
            stack.append(symbol)
            count += 1
        if symbol in [']', ')', '}']:
            if count <= 0:
                return False
            elif (symbol == ']' and stack[-1] != '[') or (symbol == '}' and stack[-1] != '{') or (symbol == ')' and stack[-1] != '('):
                return False
            else:
                stack.pop()
                count -= 1
    return count == 0


def handle_invalid_expression(expression: str, message: str, index: int) -> None:
    print("Error: {}".format(message))
    print(expression)
    for _ in range(index):
        print(" ", end="")
    print("^")
    exit(1)


def compress(expression: list) -> list:
    """
        Compress multiplications to the arrays
    """
    compressed = []
    i = 0
    n = len(expression)
    prev_compressed = False
    while i < n:
        elem = expression[i]
        if elem in ['*', '^', '&']:
            compressed[-1] = [compressed[-1], elem]
            prev_compressed = True
        elif elem in ['|', '+']:
            prev_compressed = False
            compressed.append(elem)
        elif isinstance(elem, list):
            if prev_compressed:
                unit = compressed[-1]
                unit.append(elem)
                compressed[-1] = unit
            else:
                compressed.append(elem)
        elif isinstance(elem, str):
            if prev_compressed:
                unit = compressed[-1]
                unit.append(elem)
                compressed[-1] = unit
            else:
                compressed.append(elem)
        i += 1

    return compressed


def parse_to_array(expression: str, begin, depth: int) -> list:
    """
        Divide string expression to the array with + as delimiter
    """

    n = len(expression)

    array = []
    LAST_SYMBOL = None

    if (depth != 0):
        LAST_SYMBOL = SYMBOL_TYPES.OPEN_BRACKET

    last_variable = ""
    proceed_varible = False

    to_continue = 0
    i = begin
    while (i < n):
        symbol = expression[i]
        if not symbol.isalnum() and proceed_varible:
            LAST_SYMBOL = SYMBOL_TYPES.VARIABLE
            proceed_varible = False
            array.append(last_variable)
        if symbol in ['(', '{', '[']:
            if i == n-1:
                handle_invalid_expression(expression, i)
            parsed, skip = parse_to_array(expression, i+1, depth+1)
            LAST_SYMBOL = SYMBOL_TYPES.CLOSE_BRACKET
            array.append(parsed)
            i = skip+1
            continue
        elif symbol in [')', '}', ']']:
            if depth != 0:
                to_continue = i
                break
            else:
                LAST_SYMBOL = SYMBOL_TYPES.CLOSE_BRACKET
        elif symbol in ["+", "-", "*", "^", '|', '&']:
            if LAST_SYMBOL in [None, SYMBOL_TYPES.ARITHMETIC, SYMBOL_TYPES.NOT, SYMBOL_TYPES.OPEN_BRACKET] or i == n-1:
                handle_invalid_expression(expression, "Invalid expression:", i)
            else:
                LAST_SYMBOL = SYMBOL_TYPES.ARITHMETIC
                array.append(symbol)
        elif symbol == "~":
            if i+1 >= n:
                handle_invalid_expression(expression, "Invalid expression", i)
            save = i
            i += 1
            while i < n and expression[i] == ' ':
                i += 1
            if i == n:
                handle_invalid_expression(
                    expression, "Invalid expression", save)
            elif expression[i] != '(':
                handle_invalid_expression(
                    expression, "After ~ sign expression should be in brackets", i)
            wrap = ['~']
            parsed, to_continue = parse_to_array(expression, i+1, depth+1)
            wrap.append(parsed)
            array.append(wrap)
            LAST_SYMBOL = SYMBOL_TYPES.CLOSE_BRACKET
            i = to_continue
        elif symbol.isalnum() and proceed_varible == False:
            last_variable = symbol
            proceed_varible = True
        elif symbol.isalnum() and proceed_varible:
            last_variable += symbol

        i += 1

    if proceed_varible:
        array.append(last_variable)

    return compress(array), to_continue


def parse_to_tree(expression: list) -> TreeNode:
    """
        Form balanced binary tree from array
    """
    n = len(expression)

    if n == 0:
        return None

    if n == 2 and expression[0] == '~':
        return TreeNode('~', parse_to_tree(expression[1]))

    if n == 1 and isinstance(expression[0], list):
        return parse_to_tree(expression[0])
    elif n == 1 and isinstance(expression[0], str):
        return TreeNode(expression[0])

    mid = (n-1)//2

    if '+' in expression or '|' in expression:
        if expression[mid] in ['+', '|']:
            return TreeNode(expression[mid], parse_to_tree(expression[:mid]), parse_to_tree(expression[mid+1:]))
        elif expression[mid-1] in ['+', '|']:
            return TreeNode(expression[mid-1], parse_to_tree(expression[:mid-1]), parse_to_tree(expression[mid:]))
    if expression[mid] in ['*', '^', '&']:
        return TreeNode(expression[mid], parse_to_tree(expression[:mid]), parse_to_tree(expression[mid+1:]))
    elif expression[mid-1] in ['*', '^', '&']:
        return TreeNode(expression[mid-1], parse_to_tree(expression[:mid-2]), parse_to_tree(expression[mid:]))

    return None


def proceed_numerical(expression: list) -> int:
    n = len(expression)

    if n == 0:
        return 0

    if n == 2 and expression[0] == '~':
        return -proceed_numerical(expression[1])

    if n == 1 and isinstance(expression[0], list):
        return proceed_numerical(expression[0])
    elif n == 1 and isinstance(expression[0], str):
        return int(expression[0])

    mid = (n-1)//2

    if '+' in expression or '|' in expression:
        if expression[mid] == '+':
            return proceed_numerical(expression[:mid]) + proceed_numerical(expression[mid+1:])
        elif expression[mid] == '|':
            return proceed_numerical(expression[:mid]) | proceed_numerical(expression[mid+1:])
        elif expression[mid-1] == '+':
            return proceed_numerical(expression[:mid-1]) + proceed_numerical(expression[mid:])
        elif expression[mid-1] == '|':
            return proceed_numerical(expression[:mid-1]) | proceed_numerical(expression[mid:])
    if expression[mid] in ['*', '&']:
        return proceed_numerical(expression[:mid]) * proceed_numerical(expression[mid+1:])
    elif expression[mid] == '^':
        return proceed_numerical(expression[:mid]) ^ proceed_numerical(expression[mid+1:])
    elif expression[mid-1] in ['*', '&']:
        return proceed_numerical(expression[:mid-2]) * proceed_numerical(expression[mid:])
    elif expression[mid-1] == '^':
        return proceed_numerical(expression[:mid-2]) ^ proceed_numerical(expression[mid:])


def get_left_size(node: TreeNode) -> int:
    """
        To get max depth to left from the current element
    """
    if node == None:
        return 0
    if isinstance(node.data, str) and node.data not in ['*', '+', '|', '&']:
        return 1
    return 1 + get_right_size(node.left.right) + get_left_size(node.left)


def get_right_size(node: TreeNode) -> int:
    """
        To get max depth to right from the current element
    """
    if node == None:
        return 0
    if isinstance(node.data, str) and node.data not in ['*', '+', '|', '&']:
        return 1
    return 1 + get_left_size(node.right.left) + get_right_size(node.right)


def wiring(left_x, left_y, current_x, current_y, node) -> None:
    """
        Adding wires between elements
        All wires consists of three parts and two kinks
    """
    elem_w = elem_width

    if node != None and isinstance(node.data, str) and node.data != '+' and node.data != '-':
        elem_w = 20

    y_type1 = current_y + padding
    y_type2 = left_y + elem_height//2

    if current_y <= left_y:
        y_type1 = current_y + elem_height - padding

    wires.append([[left_x+elem_w + (current_x - (left_x + elem_w))//2, y_type1,
                   left_x + elem_w + (current_x - (left_x + elem_w)) // 2, y_type1],
                  [current_x, y_type1,
                   current_x, y_type1]
                  ])
    wires.append([[left_x+elem_w + (current_x - (left_x + elem_w))//2, y_type2,
                   left_x+elem_w + (current_x - (left_x + elem_w))//2, y_type2],
                  [left_x+elem_w + (current_x - (left_x + elem_w))//2, y_type1,
                   left_x+elem_w + (current_x - (left_x + elem_w))//2, y_type1]
                  ])
    wires.append([[left_x + elem_w, y_type2,
                   left_x + elem_w, y_type2],
                  [left_x+elem_w + (current_x - (left_x + elem_w))//2, y_type2,
                   left_x+elem_w + (current_x - (left_x + elem_w))//2, y_type2]
                  ])


def proceed_elems(head: TreeNode, current_x: int, current_y: int, depth) -> None:
    """
        This function forms elems array and nodes of balanced binary tree
    """
    global elems

    if (head == None or head.data == None):
        return

    data = head.data

    if data in ['+', '|']:
        elems.append(logical_element(
            current_x, current_y, element_types.LOGICAL_OR))
    elif data in ['*', '^', '&']:
        elems.append(logical_element(
            current_x, current_y, element_types.LOGICAL_AND))
    elif data == '~':
        elems.append(logical_element(
            current_x, current_y, element_types.LOGICAL_NOT))
    elif data == '^':
        elems.append(logical_element(
            current_x, current_y, element_types.LOGICAL_XOR))
    else:
        elems.append([head.data, current_x, current_y, current_x, current_y])
        return

    right_size = get_right_size(head.left)
    left_size = get_left_size(head.right)

    left_x = current_x - x_offset
    right_x = current_x - x_offset
    left_y = current_y - (right_size - 0.5)*(y_offset + elem_height)
    right_y = current_y + (left_size - 0.5)*(y_offset + elem_height)

    if head.data == '~':
        left_y = current_y
        proceed_elems(head.left, left_x, left_y, depth+1)
        wires.append([[left_x + elem_width, left_y+elem_height//2, left_x + elem_width, left_y + elem_height//2],
                     [current_x, current_y + elem_height//2,
                         current_x, current_y + elem_height//2]
                      ])
        return

    proceed_elems(head.left, left_x,
                  left_y, depth+1)
    wiring(left_x, left_y, current_x, current_y, head.left)
    proceed_elems(head.right, right_x,
                  right_y, depth+1)
    wiring(right_x, right_y, current_x, current_y, head.right)


def print_inorder(node: TreeNode):
    if node == None:
        return
    print_inorder(node.left)
    print(node.data)
    print_inorder(node.right)


def parse_expression(expression) -> None:
    """
        Parsing string expression to array and then to balanced binary tree
    """
    if not check_brackets(expression):
        print('Brackets error')
        quit(1)

    array, to_continue = parse_to_array(expression, 0, 0)
    print(array)
    head = parse_to_tree(array)

    print_inorder(head)
    proceed_elems(head, screen_width*0.5, screen_height//2 - elem_height//2, 0)


def main() -> None:
    global viewport_scale, viewport_x, viewport_y, left_mouse_pressed, expression, screen, screen_height, screen_width, zoom_scale
    running = True

    font_size = 20

    expression = input("expression: ")

    if platform == "linux" or platform == "linux2":
        import subprocess
        cmd = ['xrandr']
        cmd2 = ['grep', '*']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(cmd2, stdin=p.stdout, stdout=subprocess.PIPE)
        p.stdout.close()
        resolution_string, junk = p2.communicate()
        resolution = resolution_string.split()[0]
        screen_width, screen_height = resolution.split('x')
        screen_width -= 50
        screen_height -= 50

    elif platform == "win32":
        import ctypes
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        screen_width, screen_height = user32.GetSystemMetrics(
            0) - 50, user32.GetSystemMetrics(1) - 50

    parse_expression(expression)

    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))

    prev_mouse_pos = pygame.mouse.get_pos()

    elems.append([expression, screen_width*0.5 + 10 + elem_width, screen_height //
                 2 - 25, screen_width*0.5 + 10 + elem_width, screen_height//2 - 25])

    line_width = 1

    while running:
        font = pygame.font.SysFont('Roboto', font_size)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                left_mouse_pressed = True

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                left_mouse_pressed = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 4:
                current_mouse_pos = pygame.mouse.get_pos()

                if zoom_scale*2 <= 16:
                    viewport_x -= current_mouse_pos[0]*zoom_scale
                    viewport_y -= current_mouse_pos[1]*zoom_scale
                    zoom_scale = zoom_scale*2
                    font_size = font_size*2

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 5:
                current_mouse_pos = pygame.mouse.get_pos()

                if zoom_scale//2 >= 1:
                    viewport_x += current_mouse_pos[0]*zoom_scale//2
                    viewport_y += current_mouse_pos[1]*zoom_scale//2
                    zoom_scale = zoom_scale//2
                    font_size = font_size//2

            elif event.type == pygame.MOUSEMOTION and left_mouse_pressed:
                current_mouse_pos = pygame.mouse.get_pos()

                viewport_x += (current_mouse_pos[0] -
                               prev_mouse_pos[0])*zoom_scale
                viewport_y += (current_mouse_pos[1] -
                               prev_mouse_pos[1])*zoom_scale

                for elem in elems:
                    if isinstance(elem, logical_element):
                        elem.x = elem.init_x + viewport_x
                        elem.y = elem.init_y + viewport_y
                    else:
                        elem[1] = elem[3] + viewport_x
                        elem[2] = elem[4] + viewport_y
                for wire in wires:
                    wire[0][0] = wire[0][2]*zoom_scale + viewport_x
                    wire[0][1] = wire[0][3]*zoom_scale + viewport_y
                    wire[1][0] = wire[1][2]*zoom_scale + viewport_x
                    wire[1][1] = wire[1][3]*zoom_scale + viewport_y

        for elem in elems:
            if isinstance(elem, logical_element):
                elem.obj = pygame.transform.scale(
                    pygame.image.load(elem.path_to_file), (elem_width*zoom_scale, elem_height*zoom_scale))
                elem.x = elem.init_x * zoom_scale + viewport_x
                elem.y = elem.init_y * zoom_scale + viewport_y
            else:
                elem[1] = elem[3]*zoom_scale + viewport_x
                elem[2] = elem[4]*zoom_scale + viewport_y

        for wire in wires:
            wire[0][0] = wire[0][2]*zoom_scale + viewport_x
            wire[0][1] = wire[0][3]*zoom_scale + viewport_y
            wire[1][0] = wire[1][2]*zoom_scale + viewport_x
            wire[1][1] = wire[1][3]*zoom_scale + viewport_y

        screen.fill(WHITE)

        for elem in elems:
            if isinstance(elem, logical_element):
                screen.blit(elem.obj, (elem.x, elem.y))
            else:
                font = pygame.font.Font('freesansbold.ttf', font_size)
                text = font.render(elem[0], True, BLACK, WHITE)
                screen.blit(text, (elem[1], elem[2] + 20))
        for wire in wires:
            pygame.draw.line(
                screen, BLACK, (wire[0][0], wire[0][1]), (wire[1][0], wire[1][1]), line_width*zoom_scale)

        prev_mouse_pos = pygame.mouse.get_pos()

        pygame.display.flip()

        time.sleep(160)


if __name__ == "__main__":
    main()
