from services.bash.handler import BashHandler

def run(bash: BashHandler, executable: str, args: list) -> int:
    kernel_name = ''
    hostname = ''
    kernel_release = ''
    kernel_version = ''
    machine_hardware = ''
    os_name = ''

    for arg in args:
        if arg == '--all':
            kernel_name = bash.get_kernel_name()
            hostname = bash.get_hostname()
            kernel_release = bash.get_kernel_release()
            kernel_version = bash.get_kernel_version()
            machine_hardware = bash.get_machine_hardware()
            os_name = bash.get_os_name()
        elif arg == '--kernel-name':
            kernel_name = bash.get_kernel_name()
        elif arg == '--nodename':
            hostname = bash.get_hostname()
        elif arg == '--kernel-release':
            kernel_release = bash.get_kernel_release()
        elif arg == '--kernel-version':
            kernel_version = bash.get_kernel_version()
        elif arg == '--machine' or arg == '--processor' or arg == '--hardware-platform':
            machine_hardware = bash.get_machine_hardware()
        elif arg == '--operating-system':
            os_name = bash.get_os_name()
        elif arg == '--help':
            bash.stdout(info['help_long'].encode('utf-8'))
            return 0
        elif arg[0] == '-':
            for miniarg in arg[1:]:
                if miniarg == 'a':
                    kernel_name = bash.get_kernel_name()
                    hostname = bash.get_hostname()
                    kernel_release = bash.get_kernel_release()
                    kernel_version = bash.get_kernel_version()
                    machine_hardware = bash.get_machine_hardware()
                    os_name = bash.get_os_name()
                elif miniarg == 's':
                    kernel_name = bash.get_kernel_name()
                elif miniarg == 'n':
                    hostname = bash.get_hostname()
                elif miniarg == 'r':
                    kernel_release = bash.get_kernel_release()
                elif miniarg == 'v':
                    kernel_release = bash.get_kernel_version()
                elif miniarg == 'm' or miniarg == 'p' or miniarg == 'i':
                    machine_hardware = bash.get_machine_hardware()
                elif miniarg == 'o':
                    os_name = bash.get_os_name()
                else:
                    bash.stderr(info['help_short'].format(miniarg).encode('utf-8'))
                    return 1
        else:
            bash.stderr(info['help_short'].format(arg.strip('-')).encode('utf-8'))
            return 1
    
    output = ''
    if kernel_name:
        output += f'{kernel_name} '
    if hostname:
        output += f'{hostname} '
    if kernel_version:
        output += f'{kernel_version} '
    if kernel_release:
        output += f'{kernel_release} '
    if machine_hardware:
        output += f'{machine_hardware} '
    if os_name:
        output += f'{os_name} '
    
    bash.stdout(output.strip().encode('utf-8'))
    return 0

info = {
    'command': 'uname',
    'path': ['/usr/bin/uname', '/bin/uname'],
    'help_long': '''Usage: uname [OPTION]...
Print certain system information.  With no OPTION, same as -s.

  -a, --all                print all information, in the following order,
                             except omit -p and -i if unknown:
  -s, --kernel-name        print the kernel name
  -n, --nodename           print the network node hostname
  -r, --kernel-release     print the kernel release
  -v, --kernel-version     print the kernel version
  -m, --machine            print the machine hardware name
  -p, --processor          print the processor type (non-portable)
  -i, --hardware-platform  print the hardware platform (non-portable)
  -o, --operating-system   print the operating system
      --help     display this help and exit
      --version  output version information and exit

GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
Report uname translation bugs to <https://translationproject.org/team/>
Full documentation at: <https://www.gnu.org/software/coreutils/uname>
or available locally via: info '(coreutils) uname invocation\'''',
    'help_short': '''uname: invalid option -- '{}'
Try 'uname --help' for more information.''',
    'run': run
}