import mmap
import contextlib
import os
import datetime
import socket


flag = True
path = "H:\\"
stack = []
count_stack = -1
OS_path = '.\\File System.bin'

class Virtual_disk:
    def initialize_virtual_disk(self):
        virtual_file = open(OS_path, "wb")
        # create a virtual disk
        for cluster in range(1024):
            for column in range(1024):
                virtual_file.write(bytes(str(0), "ascii"))


class Directory_Entry:
    dir_name = ""
    dir_attr = ""
    dir_size = 0
    dir_empty = 0
    start_cluster = 0

    def __init__(self, dir_name="", dir_attr="", dir_size=0, dir_empty=0, start_cluster=0):
        if dir_attr == "0":
            self.dir_attr = dir_attr
            dir_name_lst = dir_name.split(".")

            if len(dir_name_lst[0]) <= 7:
                self.dir_name = dir_name_lst[0] + dir_name_lst[1].upper()
            else:
                self.dir_name = dir_name_lst[0][:8] + dir_name_lst[1].upper()

        elif dir_attr == "1":
            if len(dir_name) <= 11:
                self.dir_name = dir_name
            else:
                self.dir_name = dir_name[:12]

            self.dir_attr = dir_attr

        self.dir_size = dir_size
        self.dir_empty = dir_empty
        self.start_cluster = start_cluster


class Directory(Directory_Entry):
    dir_lst = []

    def __init__(self, dir_name="", dir_attr="", dir_size=0, dir_empty=0, start_cluster=0):
        super().__init__(dir_name, dir_attr, dir_size, dir_empty, start_cluster)
        # self.parent = Directory(start_cluster=self.start_cluster)

    def write_moved_content_in_virtual_disk(self, file, fat_index, cluster=1):
        fat = Fat_Table()

        with open(OS_path, "r+") as out_file:
            with contextlib.closing(mmap.mmap(out_file.fileno(), 0)) as con:
                available_area = self.get_avaiable_index_in_cluster(cluster)

                if len(file.dir_name) < 11:
                    length = 11 - len(file.dir_name)
                    con[available_area:available_area + 11] = bytes(file.dir_name + "*" * length, "ascii")
                else:
                    con[available_area:available_area + 11] = bytes(file.dir_name[:11], "ascii")
                available_area += 11

                con[available_area:available_area + 1] = bytes(file.dir_attr, "ascii")
                available_area += 1

                start_cluster = self.convert_number_to_str(fat_index)

                con[available_area:available_area + 4] = bytes(start_cluster, "ascii")
                available_area += 4

                con[available_area:available_area + 4] = bytes(bytearray(4))
                available_area += 4

                con[available_area:available_area + 12] = bytes(bytearray(12))
                available_area += 12

    def write_copied_content_in_virtual_disk(self, file, content_index, cluster=1):
        fat = Fat_Table()
        with open(OS_path, "r+") as out_file:
            with contextlib.closing(mmap.mmap(out_file.fileno(), 0)) as con:
                available_area = self.get_avaiable_index_in_cluster(cluster)

                if len(file.dir_name) < 11:
                    length = 11 - len(file.dir_name)
                    con[available_area:available_area + 11] = bytes(file.dir_name + "*" * length, "ascii")
                else:
                    con[available_area:available_area + 11] = bytes(file.dir_name[:11], "ascii")
                available_area += 11

                con[available_area:available_area + 1] = bytes(file.dir_attr, "ascii")
                available_area += 1

                fat_available = fat.get_avaiable_index_in_Fat_table()
                fat.FAT_List[fat_available] = content_index
                start_cluster = self.convert_number_to_str(fat_available)

                con[available_area:available_area + 4] = bytes(start_cluster, "ascii")
                available_area += 4

                con[available_area:available_area + 4] = bytes(bytearray(4))
                available_area += 4

                con[available_area:available_area + 12] = bytes(bytearray(12))
                available_area += 12

    def write_content_in_virtual_disk(self, object_lst, cluster=0):
        fat = Fat_Table()

        with open(OS_path, "r+") as out_file:
            with contextlib.closing(mmap.mmap(out_file.fileno(), 0)) as con:
                for file in object_lst:

                    available_area = self.get_avaiable_index_in_cluster(cluster)
                    avaiable_index = fat.get_avaiable_index_in_Fat_table()
                    fat.set_value(avaiable_index, -1)

                    if len(file.dir_name) < 11:
                        length = 11 - len(file.dir_name)
                        con[available_area:available_area + 11] = bytes(file.dir_name + "*" * length, "ascii")
                    else:
                        con[available_area:available_area + 11] = bytes(file.dir_name[:11], "ascii")

                    available_area += 11

                    con[available_area:available_area + 1] = bytes(file.dir_attr, "ascii")
                    available_area += 1

                    start_cluster = self.convert_number_to_str(avaiable_index)

                    con[available_area:available_area + 4] = bytes(start_cluster, "ascii")
                    available_area += 4

                    con[available_area:available_area + 4] = bytes(bytearray(4))
                    available_area += 4

                    con[available_area:available_area + 12] = bytes(bytearray(12))
                    available_area += 12

    def get_avaiable_index_in_cluster(self, cluster):
        count = 0
        with open(OS_path, "r+b") as file:
            file = file.read()[(cluster + 5) * 1024:]
            while count < len(file):
                if file[count:count + 32] == b"0" * 32:
                    return count + (cluster + 5) * 1024
                count += 32

    def convert_number_to_str(self, first_cluster):
        with open(OS_path, "r+b") as file:
            with contextlib.closing(mmap.mmap(file.fileno(), 0)) as con:
                char = str(first_cluster)
                if len(char) == 1:
                    cluster = "000" + str(first_cluster)
                elif len(char) == 2:
                    cluster = "00" + str(first_cluster)
                elif len(char) == 3:
                    cluster = "0" + str(first_cluster)
                else:
                    cluster = str(first_cluster)

                return cluster

    def search_for_a_cluster_in_file_system(self):
        count = 0
        with open(OS_path, "r+b") as file:
            file = file.read()[6 * 1024:]
            while count < len(file):
                if file[count:count + 1024] == b"0" * 1024:
                    return count // 1024 + 1
                count += 1024
            else:
                print('no free space')

    def create_a_directory(self, lst):
        for direct in lst:
            directory = Directory(direct, "1", 0, 0, -1)
            self.dir_lst.append(directory)

    def create_a_file(self, lst):
        for direct in lst:
            dot_index = direct.find('.')
            if dot_index != -1:
                file = Directory(direct, "0", 0, 0, -1)
                self.dir_lst.append(file)
            else:
                print("you forgot the extension in \'", direct, "\'")

    def get_directory_details(self, folder, cluster=1):
        with open(OS_path, "r+") as file:
            clust = (cluster+5) * 1024
            file = file.read()[clust:clust+1024]

            count = 0
            while count < len(file):
                file_name = file[count:count + 11].split("*")[0]
                count += 11

                if folder == file_name and len(folder) == len(file_name):
                    attr = file[count:count + 1]
                    count += 1

                    if file[count:count + 4].find("-") != -1:
                        first_cluster = -1
                    else:
                        first_cluster = int(file[count:count + 4])
                    count += 4

                    size = int.from_bytes(file[count:count + 4].encode(), "big")
                    count += 4

                    empty = int.from_bytes(file[count:count + 12].encode(), "big")
                    count += 12

                    if not file_name.startswith("0000"):
                        if attr == "0":
                            index = file_name.find("TXT")
                            file = file_name[:index]
                            dir_file = Directory(file + ".txt", attr, size, empty, first_cluster)
                        else:
                            dir_file = Directory(file_name, attr, size, empty, first_cluster)

                    return dir_file
                else:
                    count += 21
            return None

    def get_file_details(self, folder, cluster=1):
        with open(OS_path, "r+") as file:
            clust = (cluster + 5) * 1024
            file = file.read()[clust:clust + 1024]

            count = 0
            while count < len(file):
                file_name = file[count:count + 11].split("*")[0]
                count += 11

                index = file_name.find("TXT")
                new_file = file_name[:index]+".txt"

                if folder == new_file and len(folder) == len(new_file):
                    attr = file[count:count + 1]
                    count += 1

                    if file[count:count + 4].find("-") != -1:
                        first_cluster = -1
                    else:
                        first_cluster = int(file[count:count + 4])
                    count += 4

                    size = int.from_bytes(file[count:count + 4].encode(), "big")
                    count += 4

                    empty = int.from_bytes(file[count:count + 12].encode(), "big")
                    count += 12

                    if not file_name.startswith("0000"):
                        index = file_name.find("TXT")
                        file = file_name[:index]
                        dir_file = Directory(file + ".txt", attr, size, empty, first_cluster)

                    return dir_file
                else:
                    count += 21
            return None

    def read_content_from_virtual_disk(self, cluster):
        with open(OS_path, "r+") as read_file_system:
            clust = (cluster + 5) * 1024
            read_file_system = read_file_system.read()[clust:clust + 1024]
            count = 0
            while count < len(read_file_system):
                file_name = read_file_system[count:count + 11].split("*")[0]
                count += 11

                attr = read_file_system[count:count + 1]
                count += 1

                if read_file_system[count:count + 4] != "":
                    if read_file_system[count:count + 4].find("-") != -1:
                        first_cluster = -1
                    else:
                        first_cluster = int.from_bytes(read_file_system[count:count + 4].encode(), "big")
                    count += 4

                size = int.from_bytes(read_file_system[count:count + 4].encode(), "big")
                count += 4

                if read_file_system[count:count + 12] != "":
                    empty = int.from_bytes(read_file_system[count:count + 12].encode(), "big")
                    count += 12

                if not file_name.startswith("0000"):
                    if attr == "0":
                        index = file_name.find("TXT")
                        file = file_name[:index]
                        dir_file = Directory(file + ".txt", attr, size, empty, first_cluster)
                        self.dir_lst.append(dir_file)
                        dir_file.dir_name = file + ".txt"
                    else:
                        dir_file = Directory(file_name, attr, size, empty, first_cluster)
                        self.dir_lst.append(dir_file)


            return self.dir_lst

    def read_file_content(self, cluster):
        with open(OS_path, "r+") as read_file_system:
            clust = (cluster + 5) * 1024
            read_file_content = read_file_system.read()[clust:clust + 1024]

            return read_file_content

    def search_for_a_folder(self, folder, cluster=1):
        count = 0
        clust = (cluster+5) * 1024
        with open(OS_path, "r+") as delete_folder:
            d_folder = delete_folder.read()[clust:clust+1024]
            while count < len(d_folder):
                fold = d_folder[count:count+11].split("*")[0]
                if folder == fold and len(folder) == len(fold):
                    return count

                count += 32


class File:
    content = ""

    def __init__(self, content=''):
        self.content = content.replace('\n', '*')

    def write_file_content(self, cluster):
        with open(OS_path, "r+") as out_file:
            with contextlib.closing(mmap.mmap(out_file.fileno(), 0)) as con:
                clust = (cluster + 5) * 1024
                length = len(self.content)
                con[clust:clust + 1024] = bytes('0' * 1024, 'ascii')
                con[clust:clust + length] = bytes(self.content, 'ascii')

    def clear_content(self, cluster):
        with open(OS_path, "r+") as out_file:
            with contextlib.closing(mmap.mmap(out_file.fileno(), 0)) as con:
                clust = (cluster + 5) * 1024
                con[clust:clust + 1024] = bytes('0' * 1024, 'ascii')


class Fat_Table:
    FAT_List = []

    def initialize_FAT_table(self):
        with open(OS_path, "r+b") as file:
            with contextlib.closing(mmap.mmap(file.fileno(), 0)) as con:
                con[1024:1028] = bytes("00-1", "ascii")
                con[1028:1032] = bytes("0002", "ascii")
                con[1032:1036] = bytes("0003", "ascii")
                con[1036:1040] = bytes("0004", "ascii")
                con[1040:1044] = bytes("0001", "ascii")
                con[1044:1048] = bytes("00-1", "ascii")
                con.flush()

    def read_from_file_system(self):
        with open(OS_path, "r+") as file:
            FAT_file = file.read()[1 * 1024:5 * 1024]

            count = 0
            while count < len(FAT_file):
                if FAT_file[count:count + 4].find("-") == -1:
                    self.FAT_List.append(int(FAT_file[count:count + 4]))
                else:
                    self.FAT_List.append(-1)
                count += 4

    def search_in_Fat_Table(self, clust):
        if clust in self.FAT_List:
            return self.FAT_List.index(clust)
        else:
            return None

    def get_value(self, clust):
        if 0 <= clust < len(self.FAT_List):
            return self.FAT_List[clust]

    def set_value(self, index, new_value):
        if 0 <= index < len(self.FAT_List):
            self.FAT_List[index] = new_value
        else:
            print("out of range")

    def get_avaiable_index_in_Fat_table(self):
        return self.search_in_Fat_Table(0)

    def read_from_Fat_Table(self):
        count = 1024
        with open(OS_path, "r+b") as file:
            with contextlib.closing(mmap.mmap(file.fileno(), 0)) as con:
                for i in self.FAT_List:
                    char = str(i)
                    if len(char) == 1:
                        cluster = "000" + str(i)
                    elif len(char) == 2:
                        cluster = "00" + str(i)
                    elif len(char) == 3:
                        cluster = "0" + str(i)
                    else:
                        cluster = str(i)

                    con[count:count + 4] = bytes(cluster, "ascii")
                    count += 4
                    con.flush()


def RMDIR_Command(folder_index, cluster=1):
    with open(OS_path, "r+b") as delete_folder:
        with contextlib.closing(mmap.mmap(delete_folder.fileno(), 0)) as con:
            clust = (cluster + 5) * 1024
            con[clust+folder_index:clust+folder_index+32] = bytes("0" * 32, "ascii")

def Help_Command():
    print("1- cd:", end='\t')
    print("\t\t this tool uses to change directory.", end='\n\n')

    print("2- move:", end='')
    print("\t\t this tool uses to move files.", end='\n\n')

    print("3- copy:", end='')
    print("\t\t this tool uses to copy files.", end='\n\n')

    print("4- import:", end='')
    print("\t\t this tool uses to import some data from a virtual OS.", end='\n\n')

    print("5- export:", end='')
    print("\t\t this tool uses to export some data to a virtual OS.", end='\n\n')

    print("6- dir:", end='\t')
    print("\t\t this tool uses to display the files and folders exist in the current path.", end='\n\n')

    print("7- del:", end='\t')
    print("\t\t this tool uses to remove the files.", end='\n\n')

    print("8- cls:", end='\t')
    print("\t\t this tool uses to clear screen.", end='\n\n')

    print("9- help:", end='')
    print("\t\t this tool provides Help information for Windows commands.", end='\n\n')

    print("10- touch:", end='')
    print("\t\t this tool uses to create a new file.", end='\n\n')

    print("11- rd:", end='')
    print("\t\t\t this tool uses to remove a specific directory in the current path.", end='\n\n')

    print("12- md:", end='')
    print("\t\t\t this tool uses to create a directory in the current path.", end='\n\n')

    print("13- date:", end='')
    print("\t\t show the current date and time.", end='\n\n')

    print("14- nano:", end='')
    print("\t\t this tool uses type in a text file.", end='\n\n')

    print("15- ipconfig:", end='')
    print("\t\t this tool uses display the host's name and IP.", end='\n\n')

    print("16- type:", end='\t')
    print("\t this tool uses display the file content.", end='\n\n')

    print("17- rename:", end='')
    print("\t\t this tool uses rename a file.", end='\n\n')

    print("18- quit:", end='')
    print("\t\t this tool uses shut down the shell.", end='\n\n')

def Commands_Usage(cmd):
    cmd = cmd.lower()
    if cmd == "cd":
        print("Usage:")
        print("\t Used to change directories.")
        print("\t cd followed by the file path, directory path or [..] to go back.")
        print("Example:")
        print("\t cd + [file path] | [directory path] | [..]")
        print("\t cd .. | cd [path] | cd [folder_name]")

    elif cmd == "copy":
        print("Usage:")
        print("\t Used to copy files to another directory.")
        print("\t copy followed by the file name that we want to copy, the alias name and the new path.")
        print("Example:")
        print("\t copy + [file_name] + [new_file_name] + [path]")
        print("\t copy [file_name] [file_name_1] [path]")

    elif cmd == "move":
        print("Usage:")
        print("\t Used to move files to another directory.")
        print("\t move followed by the file name that we want to move, the alias name and the new path.")
        print("Example:")
        print("\t move + [file_name] + [new_file_name] + [path]")
        print("\t move [file_name] [file_name_1] [path]")

    elif cmd == "dir":
        print("Usage:")
        print("\t Used to display the files and folders exist in the current path.")
        print("Example:")
        print("\t - you can use it by simply type a [dir] command, it will display the content of the current path")
        print('\t - dir [path], to display the content of another path')

    elif cmd == "cls":
        print("Usage:")
        print("\t Used to clear the screen.")
        print("Example:")
        print("\t you can use it by simply type a [cls] command")

    elif cmd == "del":
        print("Usage:")
        print("\t Used to remove a files.")
        print("\t del followed by the file name or the path that we want to delete.")
        print("Example:")
        print("\t del [file_name] | [path]")

    elif cmd == "touch":
        print("Usage:")
        print("\t this tool uses to create a new file.")
        print("Example:")
        print("\t touch [file(s)]")

    elif cmd == "md":
        print("Usage:")
        print("\t this tool uses to create a directory in the current path.")
        print("Example:")
        print("\t md [directory]")

    elif cmd == "rd":
        print("Usage:")
        print("\t this tool uses to remove a specific directory in the current path.")
        print("Example:")
        print("\t rd [directory]")

    elif cmd == 'date':
        print("Usage:")
        print("\t show the current date and time.")
        print("Example:")
        print("\t date")

    elif cmd == 'rename':
        print("Usage:")
        print("\t rename a specific file or directory.")
        print("Example:")
        print("\t rename [old_file_name] + [new_file_name] | [old_directory_name] + [new_directory_name]")

    elif cmd == 'import':
        print("Usage:")
        print("\t this tool uses to import some data from a virtual OS.")
        print("Example:")
        print("\t import [file's path from your OS] [path in your file system] [file's alias name]")

    elif cmd == 'export':
        print("Usage:")
        print("\t this tool uses to export some data to a virtual OS.")
        print("Example:")
        print("\t export [file from your file system] [file's path in your OS] [file's alias name]")

    elif cmd == 'nano':
        print("Usage:")
        print("\t this tool uses type in a text file.")
        print("Example:")
        print("\t nano [file name]")

    elif cmd == 'ipconfig':
        print("Usage:")
        print("\t this tool uses display the host's name and IP.")
        print("Example:")
        print("\t ipconfig")

    elif cmd == 'type':
        print("Usage:")
        print("\t this tool uses display the file content.")
        print("Example:")
        print("\t type [file_name]")

    elif cmd == "quit":
        print("Usage:")
        print("\t Used to shut down the shell.")
        print("Example:")
        print("\t you can use it by simply type a [quit] command")

def Rename_Dir_Command(new_name, folder_index, cluster=1):
    with open(OS_path, "r+b") as delete_folder:
        with contextlib.closing(mmap.mmap(delete_folder.fileno(), 0)) as con:
            clust = (cluster + 5) * 1024
            length = 0
            if len(new_name) <= 11:
                length = 11 - len(new_name)
            elif len(new_name) > 11:
                new_name = new_name[:11]

            con[clust+folder_index:clust+folder_index+11] = bytes(new_name + '*'*length, "ascii")

def Rename_File_Command(new_name, file_index, cluster=1):
    with open(OS_path, "r+b") as delete_folder:
        with contextlib.closing(mmap.mmap(delete_folder.fileno(), 0)) as con:
            clust = (cluster + 5) * 1024

            dir_name_lst = new_name.split(".")

            if len(dir_name_lst[0]) <= 7:
                dir_name = dir_name_lst[0] + dir_name_lst[1].upper()
            else:
                dir_name = dir_name_lst[0][:7] + dir_name_lst[1].upper()

            length = 11 - len(dir_name)
            if length < 0:
                length = 0

            con[clust+file_index:clust+file_index+11] = bytes(dir_name + '*'*length, "ascii")

def Draw():
    print("           -----------------------------------------------------           ")
    print("          /                                                     \\         ")
    print("         /       ----------------------------------------        \\        ")
    print("        /      /           Welcome To Our CMD             \\       \\      ")
    print("       |      |  1- Type help command to see some hints.   |       |      ")
    print("       |      |  2- Type help command followed by another  |       |      ")
    print("       |      |     command to see the usage and example   |       |      ")
    print("       |      |     for that commend.                      |       |      ")
    print("       |      |  3- If you want to terminate the program   |       |      ")
    print("       |      |     type quit command.                     |       |      ")
    print("        \\      \\                                          /       /     ")
    print("         \\       ----------------------------------------        /        ")
    print("          \\             Created By: Whoami                      /         ")
    print("           -----------------------------------------------------           ")

def Check_Path(current_path, file_name=""):
    try:
        if file_name == "F:\\" or file_name == "C:\\" or file_name == "D:\\":
            return True
        else:
            open(current_path + file_name)
    except FileNotFoundError:
        print("file or directory not found")
        return False
    except PermissionError:
        pass
    except IndexError:
        print("enter the new path")
        return False
    except OSError:
        print("file or directory not found")
        return False
    return True


fat = Fat_Table()

if not Check_Path(OS_path):
    virtual = Virtual_disk()
    virtual.initialize_virtual_disk()
    fat.initialize_FAT_table()

fat.read_from_file_system()

direct = Directory()
sub_directs = direct.read_content_from_virtual_disk(fat.FAT_List[5])

open_count = 0

while flag:
    try:
        if open_count == 0:
            Draw()
        open_count += 1

        statement = input("Admin> {} # ".format(path))
        command = statement.split()

        if command[0].lower() == 'quit':
            if len(command) == 1:
                fat.read_from_Fat_Table()
                flag = False
            else:
                print("too many arguments")


        elif command[0].lower() == 'md':
            if len(command) == 1:
                print("enter some arguments ([folder's name] / [/?])")

            else:
                if command[1] == '/?':
                    Commands_Usage(command[0])
                else:
                    dir = Directory()
                    dir.dir_lst.clear()

                    for folder in command[1:]:
                        if len(stack) == 0:
                            fold = dir.get_directory_details(folder)
                        else:
                            fold = dir.get_directory_details(folder, stack[-1][1])

                        if fold is not None:
                            print(folder, 'already exists')
                            continue
                        else:
                            dir.create_a_directory([folder])

                    if len(stack) == 0:
                        free_cluster = 1
                        if fat.FAT_List[5] == -1:
                            if len(dir.dir_lst) < 32:
                                free_cluster = dir.search_for_a_cluster_in_file_system()
                                dir.write_content_in_virtual_disk(dir.dir_lst, free_cluster)
                            else:
                                count_cluster = 0
                                while count_cluster < len(dir.dir_lst):
                                    free_cluster = dir.search_for_a_cluster_in_file_system()
                                    dir.write_content_in_virtual_disk(dir.dir_lst[count_cluster:count_cluster+32], free_cluster)
                                    count_cluster += 32

                            fat.FAT_List[5] = free_cluster

                        else:
                            if len(dir.dir_lst) < 32:
                                free_cluster = dir.get_avaiable_index_in_cluster(fat.FAT_List[5])
                                dir.write_content_in_virtual_disk(dir.dir_lst, fat.FAT_List[5])
                            else:
                                count_cluster = 0
                                while count_cluster < len(dir.dir_lst):
                                    free_cluster = dir.get_avaiable_index_in_cluster(fat.FAT_List[5])
                                    dir.write_content_in_virtual_disk(dir.dir_lst[count_cluster:count_cluster+32], fat.FAT_List[5])
                                    count_cluster += 32

                    else:
                        if len(stack) == 1:
                            folder = dir.get_directory_details(stack[-1][0])
                        else:
                            folder = dir.get_directory_details(stack[-1][0], stack[-2][1])

                        cluster_number = fat.FAT_List[folder.start_cluster]
                        if cluster_number == -1:
                            free_cluster = dir.search_for_a_cluster_in_file_system()
                            fat.FAT_List[folder.start_cluster] = free_cluster
                            stack[len(stack)-1][1] = free_cluster
                            dir.write_content_in_virtual_disk(dir.dir_lst, free_cluster)
                        else:
                            dir.write_content_in_virtual_disk(dir.dir_lst, cluster_number)
                        sub_directs.clear()
                        sub_directs = dir.read_content_from_virtual_disk(cluster_number)


        elif command[0].lower() == 'touch':
            if len(command) == 1:
                print("enter some arguments ([folder's name] / [/?])")
            else:
                if command[1] == '/?':
                    Commands_Usage(command[0])
                else:
                    file = Directory()
                    file.dir_lst.clear()

                    for fil in command[1:]:
                        if len(stack) == 0:
                            fold = file.get_file_details(fil)
                        else:
                            fold = file.get_file_details(fil, stack[-1][1])

                        if fold is not None:
                            print(fil, 'already exists')
                            continue
                        else:
                            file.create_a_file([fil])


                    if len(stack) == 0:
                        free_cluster = 1
                        if fat.FAT_List[5] == -1:
                            if len(file.dir_lst) < 32:
                                free_cluster = file.search_for_a_cluster_in_file_system()
                                file.write_content_in_virtual_disk(file.dir_lst, free_cluster)
                            else:
                                count_cluster = 0
                                while count_cluster < len(file.dir_lst):
                                    free_cluster = file.search_for_a_cluster_in_file_system()
                                    file.write_content_in_virtual_disk(file.dir_lst[count_cluster:count_cluster+32], free_cluster)
                                    count_cluster += 32
                            fat.FAT_List[5] = free_cluster
                        else:
                            if len(file.dir_lst) < 32:
                                free_cluster = file.get_avaiable_index_in_cluster(fat.FAT_List[5])
                                file.write_content_in_virtual_disk(file.dir_lst, fat.FAT_List[5])
                            else:
                                count_cluster = 0
                                while count_cluster < len(file.dir_lst):
                                    free_cluster = file.get_avaiable_index_in_cluster(fat.FAT_List[5])
                                    file.write_content_in_virtual_disk(file.dir_lst[count_cluster:count_cluster+32], fat.FAT_List[5])
                                    count_cluster += 32
                    else:
                        if len(stack) == 1:
                            folder_parent = file.get_directory_details(stack[-1][0])
                        else:
                            folder_parent = file.get_directory_details(stack[-1][0], stack[-2][1])

                        cluster_number = fat.FAT_List[folder_parent.start_cluster]

                        if cluster_number == -1:
                            free_cluster = file.search_for_a_cluster_in_file_system()
                            fat.FAT_List[folder_parent.start_cluster] = free_cluster
                            stack[len(stack)-1][1] = free_cluster
                            file.write_content_in_virtual_disk(file.dir_lst, free_cluster)
                        else:
                            file.write_content_in_virtual_disk(file.dir_lst, cluster_number)
                        sub_directs.clear()
                        sub_directs = file.read_content_from_virtual_disk(cluster_number)


        elif command[0].lower() == 'cd':
            dir = Directory()
            if len(command) == 1:
                print(path)
            else:
                try:
                    if command[1] == '/?':
                        Commands_Usage(command[0])
                    else:
                        if command[1].startswith(".."):
                            slash_index = command[1].find('\\')
                            if slash_index == -1:
                                sub_directs.clear()
                                sub_directs = dir.read_content_from_virtual_disk(1)
                                stack.pop()
                                new_path = path.split("\\")
                                path = "\\".join(new_path[:-2])
                                first_cluster = 0


                                if path[-1] != "\\":
                                    path = path + "\\"

                                count_stack -= 1
                            else:
                                dots = command[1].split('\\')
                                for i in dots:
                                    sub_directs.clear()
                                    sub_directs = dir.read_content_from_virtual_disk(1)
                                    stack.pop()
                                    new_path = path.split("\\")
                                    path = "\\".join(new_path[:-2])
                                    first_cluster = 0

                                    if path[-1] != "\\":
                                        path = path + "\\"

                                    count_stack -= 1

                        else:
                            slash_index = command[1].find('\\')
                            if slash_index == -1:
                                if len(stack) == 0:
                                    folder = dir.get_directory_details(command[1])
                                else:
                                    folder = dir.get_directory_details(command[1], stack[-1][1])

                                if folder is None:
                                    print('folder not found')
                                    continue

                                cluster_number = fat.FAT_List[folder.start_cluster]

                                if folder.dir_attr == "1":
                                    if cluster_number != -1:
                                        sub_directs.clear()
                                        sub_directs = dir.read_content_from_virtual_disk(cluster_number)

                                    path = path + command[1] + "\\"
                                    stack.append([command[1], cluster_number])
                                    count_stack += 1
                                elif folder.dir_attr == "0":
                                    print("not a directory")
                            else:
                                if not command[1].startswith('H:\\'):
                                    folders = command[1].split('\\')
                                    for folder in folders:
                                        if len(stack)==0:
                                            fold = dir.get_directory_details(folder)
                                        else:
                                            fold = dir.get_directory_details(folder, stack[-1][1])
                                        if fold is None:
                                            print('folder not found')
                                            break

                                        cluster_number = fat.FAT_List[fold.start_cluster]
                                        if fold.dir_attr == "1":
                                            if cluster_number != -1:
                                                sub_directs.clear()
                                                sub_directs = dir.read_content_from_virtual_disk(cluster_number)
                                            path = path + folder + "\\"
                                            stack.append([folder, cluster_number])
                                            count_stack += 1
                                        elif fold.dir_attr == "0":
                                            print("not a directory")
                                else:
                                    folders = command[1].split('\\')
                                    if command[1] == 'H:\\':
                                        path = 'H:\\'
                                        stack.clear()
                                    else:
                                        path = "H:\\"
                                        stack.clear()
                                        for folder in folders[1:]:
                                            if len(stack) == 0:
                                                fold = dir.get_directory_details(folder)
                                            else:
                                                fold = dir.get_directory_details(folder, stack[-1][1])

                                            if fold is None:
                                                print('folder not found')
                                                break

                                            cluster_number = fat.FAT_List[fold.start_cluster]
                                            if fold.dir_attr == "1":
                                                if cluster_number != -1:
                                                    sub_directs.clear()
                                                    sub_directs = dir.read_content_from_virtual_disk(cluster_number)
                                                path = path + folder + "\\"
                                                stack.append([folder, cluster_number])
                                                count_stack += 1
                                            elif fold.dir_attr == "0":
                                                print("not a directory")
                except:
                    print("directory not found")


        elif command[0].lower() == 'dir':
            count_files = 0
            count_folders = 0
            total_sum = 0
            dir_stack = []
            dir = Directory()

            if len(command) == 2 and command[1] == '/?':
                Commands_Usage(command[0])

            elif len(command) == 2 and command[1] != '/?':
                if command[1].startswith('H:\\'):
                    dir_folders = command[1].split('\\')

                    if command[1] == 'H:\\':
                        sub_directs.clear()
                        sub_directs = dir.read_content_from_virtual_disk(1)
                    else:
                        for folder in dir_folders[1:]:
                            if len(dir_stack) == 0:
                                fold = dir.get_directory_details(folder)
                            else:
                                fold = dir.get_directory_details(folder, dir_stack[-1][1])

                            if fold is None:
                                print('folder not found')
                                break

                            cluster_number = fat.FAT_List[fold.start_cluster]
                            dir_stack.append([folder, cluster_number])
                            sub_directs.clear()
                            sub_directs = dir.read_content_from_virtual_disk(cluster_number)

                    if len(sub_directs) > 0:
                        for folder in sub_directs:
                            if folder.dir_attr == "1":
                                print(folder.dir_name, "   <DIR>")
                                count_folders += 1
                            else:
                                if len(dir_stack) == 0:
                                    file = dir.get_file_details(folder.dir_name)
                                else:
                                    file = dir.get_file_details(folder.dir_name, dir_stack[-1][1])

                                if file is None:
                                    print('file not found')
                                    break

                                cluster = fat.FAT_List[file.start_cluster]
                                content = dir.read_file_content(cluster)
                                content = content.strip('0').split('*')
                                count_files += 1
                                print(folder.dir_name, end='   ')

                                sum_bytes = 0
                                for line in content:
                                    for char in line:
                                        sum_bytes += 1
                                        total_sum += 1

                                print(sum_bytes, 'Bytes')

                    print()
                    print('\t\t\t - ', count_folders, 'Folders')
                    print('\t\t\t - ', count_files, 'Files    ', total_sum, 'Bytes')

            elif len(command) == 1:
                if len(stack) == 0:
                    sub_directs.clear()
                    sub_directs = dir.read_content_from_virtual_disk(1)

                else:
                    folder = Directory()
                    if len(stack) == 1:
                        folder = dir.get_directory_details(stack[-1][0])
                    else:
                        folder = dir.get_directory_details(stack[-1][0], stack[-2][1])

                    if folder is None:
                        print('folder not found')
                        continue

                    cluster_number = fat.FAT_List[folder.start_cluster]
                    sub_directs.clear()
                    sub_directs = dir.read_content_from_virtual_disk(cluster_number)

                if len(sub_directs) > 0:
                    for folder in sub_directs:
                        if folder.dir_attr == "1":
                            print(folder.dir_name, "   <DIR>")
                            count_folders += 1
                        else:
                            if len(stack) == 0:
                                file = dir.get_file_details(folder.dir_name)
                            else:
                                file = dir.get_file_details(folder.dir_name, stack[-1][1])

                            if file is None:
                                print('no content')
                                break

                            cluster = fat.FAT_List[file.start_cluster]

                            content = dir.read_file_content(cluster)
                            content = content.strip('0').split('*')

                            print(folder.dir_name, end='   ')
                            count_files += 1

                            sum_bytes = 0
                            for line in content:
                                for char in line:
                                    sum_bytes += 1
                                    total_sum += 1

                            print(sum_bytes, 'Bytes')

                    print()
                    print('\t\t\t - ', count_folders, ' Folders')
                    print('\t\t\t - ', count_files, ' Files    ', total_sum, 'Bytes')
                sub_directs.clear()
            elif len(command) > 2:
                print("something goes wrong, try again")


        elif command[0].lower() == "rd":
            if len(command) == 2 and command[1] == '/?':
                Commands_Usage(command[0])
            elif len(command) == 1:
                print('enter some folders')
            else:
                try:
                    dir = Directory()
                    for one_folder in command[1:]:
                        if len(stack) == 0:
                            folder = dir.get_directory_details(one_folder)
                        else:
                            folder = dir.get_directory_details(one_folder, stack[-1][1])

                        if folder is None:
                            print('folder not found')
                            break

                        if folder.dir_attr == "1":
                            if len(stack) == 0:
                                folder_index = dir.search_for_a_folder(folder.dir_name)

                                cluster = fat.FAT_List[folder.start_cluster]
                                sub_directs.clear()
                                if len(dir.read_content_from_virtual_disk(cluster)) == 0:
                                    fat.FAT_List[folder.start_cluster] = -1

                                if fat.FAT_List[folder.start_cluster] == -1:
                                    fat.FAT_List[folder.start_cluster] = 0
                                    RMDIR_Command(folder_index)
                                    print("Deleted Successfully")
                                else:
                                    print("folder not empty")
                            else:
                                folder_index = dir.search_for_a_folder(folder.dir_name, stack[len(stack)-1][1])

                                cluster = fat.FAT_List[folder.start_cluster]
                                sub_directs.clear()
                                if len(dir.read_content_from_virtual_disk(cluster)) == 0:
                                    fat.FAT_List[folder.start_cluster] = -1

                                if fat.FAT_List[folder.start_cluster] == -1:
                                    fat.FAT_List[folder.start_cluster] = 0
                                    RMDIR_Command(folder_index, stack[len(stack) - 1][1])
                                    sub_directs.clear()
                                    sub_directs = dir.read_content_from_virtual_disk(stack[len(stack)-1][1])
                                    print("Deleted Successfully")
                                else:
                                    print("folder not empty")


                        elif folder.dir_attr == "0":
                            print("not a directory")
                except:
                    print("directory not fount")


        elif command[0].lower() == "del":
            if len(command) == 2 and command[1] == '/?':
                Commands_Usage(command[0])
            else:
                try:
                    dir = Directory()
                    for one_file in command[1:]:
                        dot_index = one_file.find('.')
                        if dot_index != -1:
                            if len(stack) == 0:
                                file = dir.get_file_details(one_file)
                            else:
                                file = dir.get_file_details(one_file, stack[-1][1])

                            if file is None:
                                print('file not found')
                                break

                            if file.dir_attr == "0":
                                if len(stack) == 0:
                                    file_index = dir.search_for_a_folder(file.dir_name)

                                    clear_cluster = fat.FAT_List[file.start_cluster]
                                    deleted_file = File()
                                    deleted_file.clear_content(clear_cluster)

                                    fat.FAT_List[file.start_cluster] = 0
                                    RMDIR_Command(file_index)
                                else:
                                    file_index = dir.search_for_a_folder(file.dir_name, stack[len(stack) - 1][1])

                                    clear_cluster = fat.FAT_List[file.start_cluster]
                                    deleted_file = File()
                                    deleted_file.clear_content(clear_cluster)

                                    fat.FAT_List[file.start_cluster] = 0
                                    RMDIR_Command(file_index, stack[len(stack) - 1][1])
                                    sub_directs.clear()
                                    sub_directs = dir.read_content_from_virtual_disk(stack[len(stack) - 1][1])
                                print("Deleted Successfully")

                            elif file.dir_attr == "1":
                                print("not a file")
                        else:
                            print("you forgot the extension in \'", one_file, "\'")
                except:
                    print("file not fount")


        elif command[0].lower() == 'cls':
            if len(command) == 2 and command[1] == '/?':
                Commands_Usage(command[0])
            elif len(command) == 1:
                os.system("cls")
                open_count = 0
            elif (len(command) == 2 and command[1] != "/?") or len(command) > 2:
                print("something goes wrong, try again")


        elif command[0].lower() == 'help':
            if len(command) == 1:
                Help_Command()
            elif len(command) == 2:
                Commands_Usage(command[1])
            else:
                print("too many arguments")


        elif command[0].lower() == 'copy':
            if len(command) == 2 and command[1] == '/?':
                Commands_Usage(command[0])
            elif len(command) == 4:
                copy_stack = []
                dir = Directory()

                original_file_dot_index = command[1].find('.')
                copy_file_dot_index = command[2].find('.')

                if original_file_dot_index != -1 or copy_file_dot_index != -1:
                    if len(stack) == 0:
                        original_file = dir.get_file_details(command[1])
                    else:
                        original_file = dir.get_file_details(command[1], stack[-1][1])
                    copy_file_path = command[3].split('\\')

                    if original_file is not None:
                        content = dir.read_file_content(fat.FAT_List[original_file.start_cluster])

                        for folder in copy_file_path[1:]:
                            if len(copy_stack) == 0:
                                fold = dir.get_directory_details(folder)
                            else:
                                fold = dir.get_directory_details(folder, copy_stack[-1][1])

                            if fold is None:
                                print('folder not found')
                                break

                            cluster_number = fat.FAT_List[fold.start_cluster]

                            if cluster_number == -1:
                                available_cluster = dir.search_for_a_cluster_in_file_system()
                                fat.FAT_List[fold.start_cluster] = available_cluster
                                cluster_number = available_cluster

                            if len(copy_stack) == 0:
                                folder_cluster = dir.search_for_a_folder(fold.dir_name, 1)
                                copy_stack.append([fold.dir_name, cluster_number])
                            else:
                                folder_cluster = dir.search_for_a_folder(fold.dir_name, copy_stack[len(copy_stack)-1][1])
                                copy_stack.append([fold.dir_name, cluster_number])

                        try:
                            copy_file = Directory()
                            copy_file.dir_lst.clear()
                            copy_file.create_a_file([command[2]])
                            file = File(content)

                            if len(file.content.strip('0')) == 0:
                                free_index = fat.get_avaiable_index_in_Fat_table()
                                fat.FAT_List[free_index] = -1
                                dir.write_content_in_virtual_disk(copy_file.dir_lst, copy_stack[-1][1])

                            else:
                                copy_file = Directory(command[2], "0", original_file.dir_size, original_file.dir_empty,
                                                      -1)
                                content_cluster = dir.search_for_a_cluster_in_file_system()
                                file.write_file_content(content_cluster)
                                dir.write_copied_content_in_virtual_disk(copy_file, content_cluster, copy_stack[-1][1])

                            copy_file.dir_lst.clear()
                            copy_stack.clear()
                        except:
                            pass
                    else:
                        print("file not found")
                else:
                    if original_file_dot_index == -1:
                        print("you forgot the extension in \'", command[1], "\'")
                    elif copy_file_dot_index == -1:
                        print("you forgot the extension in \'", command[2], "\'")


        elif command[0].lower() == 'move':
            if len(command) == 2 and command[1] == '/?':
                Commands_Usage(command[0])
            elif len(command) == 4:
                move_stack = []
                dir = Directory()

                original_file_dot_index = command[1].find('.')
                move_file_dot_index = command[2].find('.')

                if original_file_dot_index != -1 or move_file_dot_index != -1:
                    if len(stack) == 0:
                        original_file = dir.get_file_details(command[1])
                    else:
                        original_file = dir.get_file_details(command[1], stack[-1][1])

                    if original_file is None:
                        print('file not found')
                        continue

                    read_cluster = original_file.start_cluster

                    try:
                        if original_file.dir_attr == "0":
                            if len(stack) == 0:
                                file_index = dir.search_for_a_folder(original_file.dir_name)
                                RMDIR_Command(file_index)
                            else:
                                file_index = dir.search_for_a_folder(original_file.dir_name, stack[len(stack) - 1][1])
                                RMDIR_Command(file_index, stack[len(stack) - 1][1])
                                sub_directs.clear()
                                sub_directs = dir.read_content_from_virtual_disk(stack[len(stack) - 1][1])
                        elif original_file.dir_attr == "1":
                            print("not a file")


                        move_file_path = command[3].split('\\')

                        if original_file is not None:
                            if len(move_file_path) == 1:
                                copy_file = Directory(command[2], "0", original_file.dir_size, original_file.dir_empty,
                                                      -1)
                                dir.write_moved_content_in_virtual_disk(copy_file, read_cluster, 1)
                                move_stack.clear()
                            else:
                                for folder in move_file_path[1:]:
                                    if len(move_stack) == 0:
                                        fold = dir.get_directory_details(folder)
                                    else:
                                        fold = dir.get_directory_details(folder, move_stack[-1][1])

                                    if fold is None:
                                        print('folder not found')
                                        break

                                    cluster_number = fat.FAT_List[fold.start_cluster]

                                    if cluster_number == -1:
                                        available_cluster = dir.search_for_a_cluster_in_file_system()
                                        fat.FAT_List[fold.start_cluster] = available_cluster
                                        cluster_number = available_cluster

                                    if len(move_stack) == 0:
                                        folder_cluster = dir.search_for_a_folder(fold.dir_name, 1)
                                        move_stack.append([fold.dir_name, cluster_number])
                                    else:
                                        folder_cluster = dir.search_for_a_folder(fold.dir_name, move_stack[-1][1])
                                        move_stack.append([fold.dir_name, cluster_number])

                                try:
                                    copy_file = Directory(command[2], "0", original_file.dir_size, original_file.dir_empty,
                                                          -1)

                                    dir.write_moved_content_in_virtual_disk(copy_file, read_cluster, move_stack[-1][1])
                                    move_stack.clear()
                                except:
                                    pass
                        else:
                            print("file not found")

                    except:
                        print("file not fount")

                else:
                    if original_file_dot_index == -1:
                        print("you forgot the extension in \'", command[1], "\'")
                    elif move_file_dot_index == -1:
                        print("you forgot the extension in \'", command[2], "\'")


        elif command[0].lower() == 'date':
            if len(command) == 1:
                print(datetime.datetime.now())
            elif len(command) == 2  and command[1] == '/?':
                Commands_Usage(command[0])
            else:
                print('too many arguments')


        elif command[0].lower() == 'import':
            dir = Directory()
            if len(command) == 2 and command[1] == '/?':
                Commands_Usage(command[0])

            elif len(command) == 2 and command[1] != '/?':
                if Check_Path(command[1]):
                    import_file = open(command[1], 'r+').read()
                    file_name = command[1].split('\\')[-1]
                    dir.dir_lst.clear()
                    dir.create_a_file([file_name])

                    if len(stack) == 0:
                        if fat.FAT_List[5] == -1:
                            free_cluster = dir.search_for_a_cluster_in_file_system()
                            dir.write_content_in_virtual_disk(dir.dir_lst, free_cluster)
                            fat.FAT_List[5] = free_cluster
                        else:
                            dir.write_content_in_virtual_disk(dir.dir_lst, fat.FAT_List[5])

                    else:
                        if stack[-1][1] == -1:
                            free_cluster = dir.search_for_a_cluster_in_file_system()
                            dir.write_content_in_virtual_disk(dir.dir_lst, free_cluster)

                            folder_details = dir.get_directory_details(stack[-1][0], stack[-1][1])

                            if folder_details is None:
                                print('folder not found')
                                continue

                            fat.FAT_List[folder_details.start_cluster] = free_cluster
                        else:
                            folder_details = dir.get_directory_details(stack[-1][0])

                            if folder_details is None:
                                print('folder not found')
                                continue

                            cluster_number = fat.FAT_List[folder_details.start_cluster]
                            dir.write_content_in_virtual_disk(dir.dir_lst, cluster_number)

                    file = File(import_file)
                    free_cluster = dir.search_for_a_cluster_in_file_system()
                    file_details = dir.get_file_details(file_name)

                    if file_details is None:
                        print('file not found')
                        continue

                    if len(file.content) != 0:
                        fat.FAT_List[file_details.start_cluster] = free_cluster
                        file.write_file_content(free_cluster)
                    else:
                        fat.FAT_List[file_details.start_cluster] = -1

                else:
                    print('wrong path')


            elif len(command) == 3:
                if Check_Path(command[1]):
                    import_file = open(command[1], 'r+').read()
                    file_name = command[1].split('\\')[-1]
                    import_to_path = command[2].split('\\')[1:]
                    import_stack = []
                    cluster_number = -1
                    folder_details = Directory()
                    sign = True

                    dir.dir_lst.clear()
                    dir.create_a_file([file_name])

                    for folder in import_to_path:
                        if len(import_stack) == 0:
                            folder_details = dir.get_directory_details(folder)
                        else:
                            folder_details = dir.get_directory_details(folder, import_stack[-1][1])

                        if folder_details is None:
                            sign = False
                            print('folder not found')
                            break

                        cluster_number = fat.FAT_List[folder_details.start_cluster]
                        import_stack.append([folder, cluster_number])

                    if sign:
                        if cluster_number == -1:
                            free_cluster = dir.search_for_a_cluster_in_file_system()
                            fat.FAT_List[folder_details.start_cluster] = free_cluster
                            cluster_number = free_cluster
                            dir.write_content_in_virtual_disk(dir.dir_lst, free_cluster)
                        else:
                            dir.write_content_in_virtual_disk(dir.dir_lst, cluster_number)

                        file = File(import_file)
                        free_cluster = dir.search_for_a_cluster_in_file_system()
                        file_details = dir.get_file_details(file_name, cluster_number)
                        if len(file.content) != 0:
                            fat.FAT_List[file_details.start_cluster] = free_cluster
                            file.write_file_content(free_cluster)
                        else:
                            fat.FAT_List[file_details.start_cluster] = -1
                else:
                    print('wrong path')

            elif len(command) == 4:
                if Check_Path(command[1]):
                    import_file = open(command[1], 'r+').read()
                    import_to_path = command[2].split('\\')[1:]
                    import_stack = []
                    cluster_number = -1
                    folder_details = Directory()
                    sign = True

                    dir.dir_lst.clear()
                    dir.create_a_file([command[3]])

                    for folder in import_to_path:
                        if len(import_stack) == 0:
                            folder_details = dir.get_directory_details(folder)
                        else:
                            folder_details = dir.get_directory_details(folder, import_stack[-1][1])

                        if folder_details is None:
                            sign = False
                            print('folder not found')
                            break

                        cluster_number = fat.FAT_List[folder_details.start_cluster]
                        import_stack.append([folder, cluster_number])

                    if sign:
                        if cluster_number == -1:
                            free_cluster = dir.search_for_a_cluster_in_file_system()
                            fat.FAT_List[folder_details.start_cluster] = free_cluster
                            cluster_number = free_cluster
                            dir.write_content_in_virtual_disk(dir.dir_lst, free_cluster)
                        else:
                            dir.write_content_in_virtual_disk(dir.dir_lst, cluster_number)

                        file = File(import_file)
                        free_cluster = dir.search_for_a_cluster_in_file_system()
                        file_details = dir.get_file_details(command[3], cluster_number)

                        if len(file.content) != 0:
                            fat.FAT_List[file_details.start_cluster] = free_cluster
                            file.write_file_content(free_cluster)
                        else:
                            fat.FAT_List[file_details.start_cluster] = -1
                else:
                    print('wrong path')

            elif len(command) == 1:
                print('enter the files name')
            else:
                print('too many arguments')


        elif command[0].lower() == 'export':
            dir = Directory()
            export_stack = []
            sign = True
            folder_details = Directory()

            if len(command) == 2 and command[1] == '/?':
                Commands_Usage(command[0])

            elif len(command) == 3:
                if command[1].startswith('H:\\'):
                    export_path = command[1].split('\\')[1:]
                    for folder in export_path[:-1]:
                        if len(export_stack) == 0:
                            folder_details = dir.get_directory_details(folder)
                        else:
                            folder_details = dir.get_directory_details(folder, export_stack[-1][1])

                        if folder_details is None:
                            sign = False
                            print('folder not found')
                            break

                        cluster_number = fat.FAT_List[folder_details.start_cluster]
                        export_stack.append([folder, cluster_number])

                    if sign:
                        file_details = dir.get_file_details(export_path[-1], export_stack[-1][1])
                        if file_details is None:
                            print('file not found')
                        else:
                            cluster_number = fat.FAT_List[file_details.start_cluster]
                            file_content = dir.read_file_content(cluster_number).strip('0').replace('*', '\n')

                            new_file = open(command[2]+'\\'+export_path[-1], 'w+')
                            new_file.write(file_content)
                            new_file.close()
                else:
                    if len(stack) == 0:
                        file_details = dir.get_file_details(command[1])
                    else:
                        file_details = dir.get_file_details(command[1], stack[-1][1])

                    if file_details is None:
                        print('file not found')
                    else:
                        cluster_number = fat.FAT_List[file_details.start_cluster]
                        file_content = dir.read_file_content(cluster_number).strip('0').replace('*', '\n')

                        new_file = open(command[2]+'\\'+command[1], 'w+')
                        new_file.write(file_content)
                        new_file.close()


            elif len(command) == 4:
                if command[1].startswith('H:\\'):
                    export_path = command[1].split('\\')[1:]
                    for folder in export_path[:-1]:
                        if len(export_stack) == 0:
                            folder_details = dir.get_directory_details(folder)
                        else:
                            folder_details = dir.get_directory_details(folder, export_stack[-1][1])

                        if folder_details is None:
                            sign = False
                            print('folder not found')
                            break

                        cluster_number = fat.FAT_List[folder_details.start_cluster]
                        export_stack.append([folder, cluster_number])


                    if sign:
                        file_details = dir.get_file_details(export_path[-1], export_stack[-1][1])
                        if file_details is None:
                            print('file not found')
                        else:
                            cluster_number = fat.FAT_List[folder_details.start_cluster]
                            file_content = dir.read_file_content(cluster_number).strip('0').replace('*', '\n')
                            new_file = open(command[2]+'\\'+command[3], 'w+')
                            new_file.write(file_content)
                            new_file.close()
                else:
                    if len(stack) == 0:
                        file_details = dir.get_file_details(command[1])
                    else:
                        file_details = dir.get_file_details(command[1], stack[-1][1])

                    if file_details is None:
                        print('file not found')
                    else:
                        cluster_number = fat.FAT_List[file_details.start_cluster]
                        file_content = dir.read_file_content(cluster_number).strip('0').replace('*', '\n')
                        new_file = open(command[2] + '\\' + command[3], 'w+')
                        new_file.write(file_content)
                        new_file.close()


            elif len(command) == 1:
                print('enter the files name')
            elif len(command) > 4:
                print('too many arguments')


        elif command[0].lower() == 'rename':
            if len(command) == 2 and command[1] == '/?':
                Commands_Usage(command[0])

            elif len(command) == 3:
                dir = Directory()
                folder_details = Directory()
                if command[1].find('.') == -1 and command[2].find('.') == -1:
                    if len(stack) == 0:
                        file_details = dir.get_directory_details(command[1])
                    else:
                        file_details = dir.get_directory_details(command[1], stack[-1][1])

                    if folder_details is None:
                        print('folder not found')
                    else:
                        if len(stack) == 0:
                            folder_index = dir.search_for_a_folder(command[1])
                            Rename_Dir_Command(command[2], folder_index)
                        else:
                            folder_index = dir.search_for_a_folder(command[1], stack[len(stack) - 1][1])
                            Rename_Dir_Command(command[2], folder_index, stack[len(stack) - 1][1])
                        print('Changed Successfully')
                else:
                    if len(stack) == 0:
                        file_details = dir.get_file_details(command[1])
                    else:
                        file_details = dir.get_file_details(command[1], stack[-1][1])

                    if file_details is None:
                        print('file not found')
                    else:
                        file_name = command[1].split('.')
                        file_name = file_name[0] + file_name[1].upper()
                        if len(stack) == 0:
                            file_index = dir.search_for_a_folder(file_name)
                            Rename_File_Command(command[2], file_index)
                        else:
                            file_index = dir.search_for_a_folder(file_name, stack[len(stack) - 1][1])
                            Rename_File_Command(command[2], file_index, stack[len(stack) - 1][1])
                        print('Changed Successfully')

            elif len(command) == 2 and command[1] != '/?':
                print('enter the file name')
            else:
                print('too many arguments')


        elif command[0].lower() == 'nano':
            content = ''
            line = ''

            if len(command) == 2 and command[1] == '/?':
                Commands_Usage(command[0])

            elif len(command) == 2 and command[1] != '/?':
                dir = Directory()

                if len(stack) == 0:
                    file_details = dir.get_file_details(command[1])
                else:
                    file_details = dir.get_file_details(command[1], stack[-1][1])

                if file_details is None:
                    print('file not found')
                else:
                    if file_details.dir_attr == '1':
                        print('not a file')
                    elif file_details.dir_attr == '0':
                        print('Enter file content, and if you want to exit enter [ :wq ]: ')
                        while line != ':wq':
                            line = input()
                            if line != ':wq':
                                content += line + '*'

                        cluster_number = fat.FAT_List[file_details.start_cluster]

                        if cluster_number == -1:
                            file = File(content)
                            free_cluster = dir.search_for_a_cluster_in_file_system()
                            fat.FAT_List[file_details.start_cluster] = free_cluster
                            file.write_file_content(free_cluster)

                        else:
                            file = File(content)
                            choice = input('do you want to delete to old content ? (y \\ n): ')
                            if choice == 'y' or choice == 'Y':
                                file.write_file_content(cluster_number)
                            elif choice == 'N' or choice == 'n':
                                old_content = dir.read_file_content(cluster_number).strip('0')
                                new_content = old_content + content
                                file = File(new_content)
                                file.write_file_content(cluster_number)

            elif len(command) == 1:
                print('enter the file name')
            else:
                print('too many arguments')


        elif command[0].lower() == 'type':
            if len(command) == 2 and command[1] == '/?':
                Commands_Usage(command[0])

            elif len(command) == 2 and command[1] != '/?':
                dir = Directory()

                if len(stack) == 0:
                    file_details = dir.get_file_details(command[1])
                else:
                    file_details = dir.get_file_details(command[1], stack[-1][1])

                if file_details is None:
                    print('file not found')
                else:
                    if file_details.dir_attr == '1':
                        print('not a file')
                    elif file_details.dir_attr == '0':
                        cluster_number = fat.FAT_List[file_details.start_cluster]

                        if cluster_number == -1:
                            print('file is empty')
                        else:
                            content = dir.read_file_content(cluster_number)
                            content = content.strip('0').split('*')

                            for line in content:
                                print(line)

            elif len(command) == 1:
                print('enter the file name')
            else:
                print('too many arguments')


        elif command[0].lower() == 'ipconfig':
            if len(command) == 2 and command[1] == '/?':
                Commands_Usage(command[0])
            elif len(command) == 1:
                host_name = socket.gethostname()
                ip_address = socket.gethostbyname(host_name)
                print("-host name:", host_name)
                print("-ip address:", ip_address)
            else:
                print("too much arguments")


        else:
            print('command not found')


    except FileNotFoundError:
        break

    except:
        pass
