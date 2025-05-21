import os
import traceback


def extract_traceback(stack_summary: traceback.StackSummary) -> str:
    list_dir_separator = '\\' if os.name == 'nt' else '/'
    work_env = os.getcwd() + list_dir_separator

    stack = []
    for frame in stack_summary:
        file_name = frame.filename
        if file_name.startswith(work_env):
            if file_name[len(work_env)] != '.':
                stack.append(f'{file_name}:{frame.lineno}:{frame.name}')

    message = ' - '.join(stack[-2:0:-1])
    message = message.replace(work_env, '').replace('\\', '/')
    return message


def extract_exception_traceback(exc: Exception) -> str:
    tb = exc.__traceback__
    work_env = os.getcwd()
    list_dir_separator = '\\' if os.name == 'nt' else '/'
    stack = []
    while tb is not None:
        file_name = tb.tb_frame.f_code.co_filename
        if file_name.startswith(f'{work_env}{list_dir_separator}.'):
            tb = tb.tb_next
            continue
        filename = tb.tb_frame.f_code.co_filename.replace(work_env, '').replace('\\', '/').replace('/', '.').strip(
            '.py')
        stack.append(f'{filename}:{tb.tb_lineno}')
        tb = tb.tb_next
    message = f'{str(exc)} \nOccurred at {'\nat '.join(stack[::-1])}'
    return message
