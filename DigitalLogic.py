import pygame

equation = ""

screen_width = 2000
screen_height = 1440

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

font_size = 26
elem_width = 30
padding = 5
elem_height = 20

screen = None

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
        path_to_file = ""
        if type == element_types.LOGICAL_AND:
            path_to_file = './and.svg'
        elif type == element_types.LOGICAL_OR:
            path_to_file = './or.svg'
        elif type == element_types.LOGICAL_NOT:
            path_to_file = './not.svg'
        self.obj = pygame.transform.scale(
            pygame.image.load(path_to_file), (elem_width, elem_height))


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


def check_brackets(equation: str) -> bool:
    """ 
        Check that all brackets from correct pairs using stack
    """
    stack = []
    count = 0
    for symbol in equation:
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


def handle_invalid_equation(equation: str, index: int) -> None:
    print("Error: Invalid equation:")
    print(equation)
    for _ in range(index):
        print(" ", end="")
    print("^")
    raise SignError()


def compress_multiplying(equation: list) -> list:
    """
        Compress multiplications to the arrays
    """
    compressed = []
    i = 0
    n = len(equation)
    prev_multiplying = False
    while i < n:
        elem = equation[i]
        if elem == '*':
            compressed[-1] = [compressed[-1], '*']
            prev_multiplying = True
        elif elem == '+':
            prev_multiplying = False
            compressed.append('+')
        elif isinstance(elem, list):
            if prev_multiplying:
                unit = compressed[-1]
                unit.append(elem)
                compressed[-1] = unit
            else:
                compressed.append(elem)
        elif isinstance(elem, str):
            if prev_multiplying:
                unit = compressed[-1]
                unit.append(elem)
                compressed[-1] = unit
            else:
                compressed.append(elem)
        i += 1

    return compressed


def parse_to_array(equation: str, begin, depth: int) -> list:
    """
        Divide string equation to the array with + as delimiter
    """

    array = []
    n = len(equation)
    LAST_SYMBOL = None

    if (depth != 0):
        LAST_SYMBOL = SYMBOL_TYPES.OPEN_BRACKET

    last_variable = ""
    proceed_varible = False

    to_continue = 0
    i = begin
    while (i < n):
        symbol = equation[i]

        if not symbol.isalnum() and proceed_varible:
            LAST_SYMBOL = SYMBOL_TYPES.VARIABLE
            proceed_varible = False
            array.append(last_variable)

        if symbol in ['(', '{', '[']:
            if i == n-1:
                handle_invalid_equation(equation, i)
            parsed, skip = parse_to_array(equation, i+1, depth+1)
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
        elif symbol in ["+", "-", "*"]:
            if LAST_SYMBOL in [None, SYMBOL_TYPES.ARITHMETIC, SYMBOL_TYPES.NOT, SYMBOL_TYPES.OPEN_BRACKET] or i == n-1:
                handle_invalid_equation(equation, i)
            else:
                LAST_SYMBOL = SYMBOL_TYPES.ARITHMETIC
                array.append(symbol)
        elif symbol.isalnum() and proceed_varible == False:
            last_variable = symbol
            proceed_varible = True
        elif symbol.isalnum() and proceed_varible:
            last_variable += symbol

        i += 1

    if proceed_varible:
        array.append(last_variable)

    return compress_multiplying(array), to_continue


def parse_to_tree(equation: list) -> TreeNode:
    """
        Form balanced binary tree from array
    """
    n = len(equation)

    if n == 0:
        return None

    if n % 2 == 0:
        print(equation)
        raise RuntimeError("Error: array is invalid for tree parsing")

    if n == 1 and isinstance(equation[0], list):
        return parse_to_tree(equation[0])
    elif n == 1 and isinstance(equation[0], str):
        return TreeNode(equation[0])

    mid = (n-1)//2

    if '+' in equation:
        if equation[mid] == '+':
            return TreeNode('+', parse_to_tree(equation[:mid]), parse_to_tree(equation[mid+1:]))
        elif equation[mid-1] == '+':
            return TreeNode('+', parse_to_tree(equation[:mid-1]), parse_to_tree(equation[mid:]))
    if equation[mid] == '*':
        return TreeNode('*', parse_to_tree(equation[:mid]), parse_to_tree(equation[mid+1:]))
    elif equation[mid-1] == '*':
        return TreeNode('*', parse_to_tree(equation[:mid-2]), parse_to_tree(equation[mid:]))

    return None


def get_left_size(node: TreeNode) -> int:
    """
        To get max depth to left from the current element
    """
    if node == None:
        return 0
    if isinstance(node.data, str) and node.data != '+' and node.data != '*':
        return 1
    return 1 + get_right_size(node.left.right) + get_left_size(node.left)


def get_right_size(node: TreeNode) -> int:
    """
        To get max depth to right from the current element
    """
    if node == None:
        return 0
    if isinstance(node.data, str) and node.data != '+' and node.data != '*':
        return 1
    return 1 + get_left_size(node.right.left) + get_right_size(node.right)


def wiring(left_x, left_y, current_x, current_y, node):
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

    if head.data == '+':
        elems.append(logical_element(
            current_x, current_y, element_types.LOGICAL_OR))
    elif head.data == '*':
        elems.append(logical_element(
            current_x, current_y, element_types.LOGICAL_AND))
    else:
        elems.append([head.data, current_x, current_y, current_x, current_y])
        return

    right_size = get_right_size(head.left)
    left_size = get_left_size(head.right)

    left_x = current_x - x_offset
    right_x = current_x - x_offset
    left_y = current_y - (right_size - 0.5)*(y_offset + elem_height)
    right_y = current_y + (left_size - 0.5)*(y_offset + elem_height)

    proceed_elems(head.left, left_x,
                  left_y, depth+1)

    wiring(left_x, left_y, current_x, current_y, head.left)

    proceed_elems(head.right, right_x,
                  right_y, depth+1)

    wiring(right_x, right_y, current_x, current_y, head.right)


def parse_equation(equation) -> None:
    """
        Parsing string equation to array and then to balanced binary tree
    """
    if not check_brackets(equation):
        print('Brackets error')
        quit(1)

    array, to_continue = parse_to_array(equation, 0, 0)
    head = parse_to_tree(array)

    proceed_elems(head, screen_width*0.5, screen_height//2 - elem_height//2, 0)


def main() -> None:
    global viewport_scale, viewport_x, viewport_y, left_mouse_pressed, equation, screen
    running = True

    equation = input("Equation: ")

    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))

    prev_mouse_pos = pygame.mouse.get_pos()

    elems.append([equation, screen_width*0.5 + 40, screen_height//2 - 17, screen_width*0.5 + 40, screen_height//2 - 17])
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
                for elem in elems:
                    if isinstance(elem, logical_element):
                        elem.x = elem.init_x + viewport_x
                        elem.y = elem.init_y + viewport_y
                    else:
                        elem[1] = elem[3] + viewport_x
                        elem[2] = elem[4] + viewport_y
                for wire in wires:
                    wire[0][0] = wire[0][2] + viewport_x
                    wire[0][1] = wire[0][3] + viewport_y
                    wire[1][0] = wire[1][2] + viewport_x
                    wire[1][1] = wire[1][3] + viewport_y

        screen.fill(WHITE)

        for elem in elems:
            if isinstance(elem, logical_element):
                screen.blit(elem.obj, (elem.x, elem.y))
            else:
                font = pygame.font.Font('freesansbold.ttf', 16)
                text = font.render(elem[0], True, BLACK, WHITE)
                screen.blit(text, (elem[1], elem[2] + text.get_height()//1.5))
        for wire in wires:
            pygame.draw.line(
                screen, BLACK, (wire[0][0], wire[0][1]), (wire[1][0], wire[1][1]))

        prev_mouse_pos = pygame.mouse.get_pos()

        pygame.display.flip()


if __name__ == "__main__":
    main()
