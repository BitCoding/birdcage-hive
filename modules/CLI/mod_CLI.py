# encoding: iso-8859-1

#
# Copyright (C) 20011-2013 by Booksize
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.
#

import CP
# Our Console

import commands
import os
import sys
import threading
import time
import string

IDENTCHARS = string.ascii_letters + string.digits + '_'

## define Checking-Thread
class Master(threading.Thread):
    check = True;
    interval = 1;
    CP #Pointer for the CP
    mod_dict = None
    prompt = "Command:"
    identchars = IDENTCHARS
    ruler = '='
    lastcmd = ''
    intro = None
    doc_leader = ""
    doc_header = "Documented commands (type help <command>):"
    misc_header = "Miscellaneous help command:"
    undoc_header = "Undocumented commands:"
    nohelp = "No help on %s"
    use_rawinput = 1


    def __init__(self,CP, completekey='tab', stdin=None, stdout=None):
        ## Set the CP
        self.CP = CP

        # Do initialization what you have to do
        threading.Thread.__init__(self)
        self.active_module = None
        #Zum idend. woher die Anfrage kam
        self.ID = "CLI"

        if stdin is not None:
            self.stdin = stdin
        else:
            self.stdin = sys.stdin

        if stdout is not None:
            self.stdout = stdout
        else:
            self.stdout = sys.stdout

        self.cmdqueue = []
        self.completekey = completekey

        return

    ##If any drones sends an init, this routine would be called
    def initfromdrone(self, args, handler):
        return

    def run(self):
        if self.use_rawinput and self.completekey:
            try:
                import readline
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey+": complete")
            except ImportError:
                pass
        try:
            while self.check:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        try:
                            if(self.active_module == None):
                                line = raw_input(self.prompt)
                            else:
                                line = raw_input(self.active_module + "/" + self.prompt)
                        except EOFError:
                            line = 'EOF'
                    else:
                        if(self.active_module == None):
                            self.stdout.write(self.prompt)
                        else:
                            self.stdout.write(self.active_module + "/" + self.prompt)
                        self.stdout.flush()
                        line = self.stdin.readline()
                        if not len(line):
                            line = 'EOF'
                        else:
                            line = line.rstrip('\r\n')
                if self.check :
                    output = self.modulcmd(line)
                    if (output):
                        self.CP.command (output, self)
                    elif not (output == False):
                        self.onecmd(line)
                self.stdout.flush()
        finally:
            self.stdout.flush()

    def clicommand(self, args):
        if (args == ""):
            return;

        #Activate our "new-style" Console
        if (self.internalCommands(args) == True and self.active_module  == ""):
            return

        if (self.active_module  == ""):
            self.writeline("Ya have to select a Module via use")
            return

        self.output = self.CP.GetDictionary(self.active_module, args)
        if (self.output):
            self.CP.command (self.output, self)
        return

    #internalCommands
    def internalCommands(self,args):
        self.omv = args.split(" ")
        self.offset = 1

        if (self.omv[0].strip() == "module"):
            self.out = ""
            try:
                if (self.omv[1].strip() == "stop"):
                    self.out = "001 2 " + self.omv[2];
                elif (self.omv[1].strip() == "start"):
                    self.out = "001 3 " + self.omv[2] ;
                elif (self.omv[1].strip() == "export"):
                    self.out = "001 4 " + self.omv[2];
                elif (self.omv[1].strip() == "export-all"):
                    self.out = "001 6"
                self.CP.command(self.out,self)
                return True
            except IndexError:
                self.writeline("Ya have to type in a modulename")
                return True

        if (args.split(" ")[0] == "cli_test"):
            try:
                self.CP.command("001 8 " + args.split(" ")[1] + " "+  args.split(" ")[2], self)
                return True
            except IndexError:
                self.writeline("TestCommand");
                return True

    def parseline(self, line):
        """Parse the line into a command name and a string containing
        the arguments.  Returns a tuple containing (command, args, line).
        'command' and 'args' may be None if the line couldn't be parsed.
        """
        line = line.strip()
        if not line:
            return None, None, line
        elif line[0] == '?':
            line = 'help ' + line[1:]
        #elif line[0] == '!':
            #if hasattr(self, 'do_shell'):
                #line = 'shell ' + line[1:]
            #else:
                #return None, None, line
        i, n = 0, len(line)
        while i < n and line[i] in self.identchars: i = i+1
        cmd, arg = line[:i], line[i:].strip()
        return cmd, arg, line

    def modulcmd(self, line):
        cmd, arg, line = self.parseline(line)

        if not line:
            return self.emptyline()
        if cmd is None:
            return self.default(line)
        self.lastcmd = line
        if line == 'EOF' :
            self.lastcmd = ''
        if cmd == '':
            return self.default(line)
        else:
            if(self.mod_dict):
                try:
                    func = getattr(self.mod_dict, 'do_' + cmd)
                    return func(arg)
                except AttributeError:
                    return self.mod_dict.get(line)
            else:
                return None
        return None

    def onecmd(self, line):
        """Interpret the argument as though it had been typed in response
        to the prompt.

        This may be overridden, but should not normally need to be;
        see the precmd() and postcmd() methods for useful execution hooks.
        The return value is a flag indicating whether interpretation of
        commands by the interpreter should stop.

        """
        cmd, arg, line = self.parseline(line)
        if not line:
            return self.emptyline()
        if cmd is None:
            return self.default(line)
        self.lastcmd = line
        if line == 'EOF' :
            self.lastcmd = ''
        if cmd == '':
            return self.default(line)
        else:
            try:
                func = getattr(self, 'do_' + cmd)
            except AttributeError:
                return self.default(line)
            return func(arg)

    def emptyline(self):
        """Called when an empty line is entered in response to the prompt.

        If this method is not overridden, it repeats the last nonempty
        command entered.

        """
        if self.lastcmd:
            return self.onecmd(self.lastcmd)

    def default(self, line):
        self.stdout.write('Unknown syntax: %s\n'%line)

    def completedefault(self, *ignored):
        return []

    def completenames(self, text, *ignored):
        dotext = 'do_'+text
        if(self.mod_dict):
            try:
                names = self.mod_dict.get_names()
                if(names):
                    ret = [a[3:] for a in self.get_names() if a.startswith(dotext)]
                    ret = ret + [b[3:] for b in names if b.startswith(dotext)]
                    return ret
                else:
                     return [a[3:] for a in self.get_names() if a.startswith(dotext)]
            except AttributeError:
                return [a[3:] for a in self.get_names() if a.startswith(dotext)]
        else:
            return [a[3:] for a in self.get_names() if a.startswith(dotext)]

    def complete(self, text, state):
        """Return the next possible completion for 'text'.

        If a command has not been entered, then complete against command list.
        Otherwise try to call complete_<command> to get list of completions.
        """
        if state == 0:
            import readline
            origline = readline.get_line_buffer()
            line = origline.lstrip()
            stripped = len(origline) - len(line)
            begidx = readline.get_begidx() - stripped
            endidx = readline.get_endidx() - stripped
            if begidx>0:
                cmd, args, foo = self.parseline(line)
                if cmd == '':
                    compfunc = self.completedefault
                else:
                    try:
                        if(self.mod_dict):
                            try:
                                compfunc = getattr(self.mod_dict, 'complete_' + cmd)
                            except AttributeError:
                                compfunc = getattr(self, 'complete_' + cmd)
                        else:
                            compfunc = getattr(self, 'complete_' + cmd)
                    except AttributeError:
                        compfunc = self.completedefault
            else:
                compfunc = self.completenames
            self.completion_matches = compfunc(text, line, begidx, endidx)
        try:
            return self.completion_matches[state]
        except IndexError:
            return None

    def get_names(self):
        # This method used to pull in base class attributes
        # at a time dir() didn't do it yet.
        return dir(self.__class__)

    def complete_help(self, *args):
        commands = set(self.completenames(*args))
        topics = set(a[5:] for a in self.get_names()
                     if a.startswith('help_' + args[0]))
        return list(commands | topics)

    #default commands
    def help_quit(self):
        print '\n'.join([ 'quit',
                          'Shut Up And Take My Money',
                        ])

    def do_quit(self, arg):
        self.CP.command("TP",self)
        self.writeline("terminating...")
        self.check = False
        return

    def help_print(self):
        print '\n'.join([ 'print',
                          '',
                        ])

    def do_print(self, arg):
        print '\n'.join([ arg,
                        ])
        return

    def help_exit(self):
        print '\n'.join([ 'exit',
                          'Exit the Active Modul',
                        ])

    def do_exit(self, arg):
        if(self.active_module == None):
            print '\n'.join([ 'None Active Modul',])
            self.mod_dict = None
        else:
           print '\n'.join([ 'Exit ' + self.active_module,])
           self.active_module = None
           self.mod_dict = None
        return

    LIST = [ 'modules', 'drones']

    def complete_list(self, text, line, begidx, endidx):
        if not text:
            completions = self.LIST[:]
        else:
            completions = [ f
                            for f in self.LIST
                            if f.startswith(text)
                            ]
        return completions

    def help_list(self):
        print '\n'.join([ 'list [modules/drones]',
                          'List what? Would ya like to see the modules?',
                        ])

    def do_list(self, arg):
        if arg:
            # XXX check arg syntax
            if(arg == "modules"):
                for f in self.CP.installed_mods:
                    if not (f[3] == "mod_CLI"):
                        self.stdout.write('%s\n'%f[3])
            elif (arg == "drones"):
                for f in self.CP.m_Sock.DroneUpdater.KnownDronesName:
                    self.stdout.write('%s\n'%f)
            return
        else:
            func = getattr(self, 'help_list')
            func()
        return

    def do_module(self,arg):
        if (self.active_module  == ""):
            func = getattr(self, 'help_use')

        return

    def complete_use(self, text, line, begidx, endidx):
        completions = []
        if not text:
            for f in self.CP.installed_mods:
                if not (f[3] == "mod_CLI"):
                    completions.append(f[3])
        else:
            for f in self.CP.installed_mods:
                if not (f[3] == "mod_CLI"):
                    if(f[3].startswith(text)):
                        completions.append(f[3])

        return completions

    def help_use(self):
        print '\n'.join([ 'use [module]',
                          'Ya have to select a Module via use',
                        ])

    def do_use(self, arg):
        if arg:
            modul = None
            handler = None
            for f in self.CP.installed_mods:
                if(f[3] == arg):
                    modul = f[3]
                    try:
                        handler = f[1].getInstance()
                    except AttributeError:
                        handler = None
           
            if(modul == None or modul == "mod_CLI"):
                print '\n'.join([  'Modul doesn´t exist!',
                                   'use list modules to find installed Moduls',
                        ])
            else:
                self.active_module = arg
                dict = self.CP.GetDictionary(self.active_module)
                if(dict):
                    try:
                        dict.initIT(self.CP,self,handler)
                        self.mod_dict = dict
                    except AttributeError:
                        self.mod_dict = dict
                else:
                    self.mod_dict = None
            return
        else:
            func = getattr(self, 'help_use')
            func()
        return

    def do_help(self, arg):
        'List available commands with "help" or detailed help with "help cmd".'
        if arg:
            # XXX check arg syntax
            try:
                if(self.mod_dict):
                    try:
                        func = getattr(self.mod_dict, 'help_' + arg)
                        func()
                        return
                    except AttributeError:
                        func = getattr(self, 'help_' + arg)
            except AttributeError:
                try:
                    doc=getattr(self, 'do_' + arg).__doc__
                    if doc:
                        self.stdout.write("%s\n"%str(doc))
                        return
                except AttributeError:
                    pass
                self.stdout.write("%s\n"%str(self.nohelp % (arg,)))
                return
            func()
        else:
            names = self.get_names()
            names_mod = []
            cmds_doc = []
            cmds_undoc = []
            help = {}
            for name in names:
                if name[:5] == 'help_':
                    help[name[5:]]=1
            if(self.mod_dict):
                try:
                    names_mod = self.mod_dict.get_names()
                    for name in names_mod:
                        if name[:5] == 'help_':
                            help[name[5:]]=1
                except AttributeError:
                    names_mod = []
            names.sort()
            names_mod.sort()
            # There can be duplicates if routines overridden
            prevname = ''
            for name in names:
                if name[:3] == 'do_':
                    if name == prevname:
                        continue
                    prevname = name
                    cmd=name[3:]
                    if cmd in help:
                        cmds_doc.append(cmd)
                        del help[cmd]
                    elif getattr(self, name).__doc__:
                        cmds_doc.append(cmd)
                    else:
                        cmds_undoc.append(cmd)
            if(self.mod_dict):
                for name in names_mod:
                    if name[:3] == 'do_':
                        if name == prevname:
                            continue
                        prevname = name
                        cmd=name[3:]
                        if cmd in help:
                            cmds_doc.append(cmd)
                            del help[cmd]
                        elif getattr(self, name).__doc__:
                            cmds_doc.append(cmd)
                        else:
                            cmds_undoc.append(cmd)
                            
            self.stdout.write("%s\n"%str(self.doc_leader))
            self.print_topics(self.doc_header,   cmds_doc,   15,80)
            self.print_topics(self.misc_header,  help.keys(),15,80)
            self.print_topics(self.undoc_header, cmds_undoc, 15,80)

    def print_topics(self, header, cmds, cmdlen, maxcol):
        if cmds:
            self.stdout.write("%s\n"%str(header))
            if self.ruler:
                self.stdout.write("%s\n"%str(self.ruler * len(header)))
            self.columnize(cmds, maxcol-1)
            self.stdout.write("\n")

    def columnize(self, list, displaywidth=80):
        """Display a list of strings as a compact set of columns.

        Each column is only as wide as necessary.
        Columns are separated by two spaces (one was not legible enough).
        """
        if not list:
            self.stdout.write("<empty>\n")
            return
        nonstrings = [i for i in range(len(list))
                        if not isinstance(list[i], str)]
        if nonstrings:
            raise TypeError, ("list[i] not a string for i in %s" %
                              ", ".join(map(str, nonstrings)))
        size = len(list)
        if size == 1:
            self.stdout.write('%s\n'%str(list[0]))
            return
        # Try every row count from 1 upwards
        for nrows in range(1, len(list)):
            ncols = (size+nrows-1) // nrows
            colwidths = []
            totwidth = -2
            for col in range(ncols):
                colwidth = 0
                for row in range(nrows):
                    i = row + nrows*col
                    if i >= size:
                        break
                    x = list[i]
                    colwidth = max(colwidth, len(x))
                colwidths.append(colwidth)
                totwidth += colwidth + 2
                if totwidth > displaywidth:
                    break
            if totwidth <= displaywidth:
                break
        else:
            nrows = len(list)
            ncols = 1
            colwidths = [0]
        for row in range(nrows):
            texts = []
            for col in range(ncols):
                i = row + nrows*col
                if i >= size:
                    x = ""
                else:
                    x = list[i]
                texts.append(x)
            while texts and not texts[-1]:
                del texts[-1]
            for col in range(len(texts)):
                texts[col] = texts[col].ljust(colwidths[col])
            self.stdout.write("%s\n"%str("  ".join(texts)))

    #write a line to our CLI
    def writeline(self,args,endt = False):
        cmd, arg, line = self.parseline(args)
        self.stdout.write("\n")
        if(cmd == "PRINT"):
            self.stdout.write("%s"%str("".join(arg)))
        else:
            self.stdout.write("%s"%str("".join(line)))

        if(endt):
            self.stdout.write("\n")
            if(self.active_module == None):
                self.stdout.write(self.prompt)
            else:
                self.stdout.write(self.active_module + "/" + self.prompt)
            self.stdout.flush()

    def config(self, args, CP):
        return

    def command(self,args, handler):
        return

    def update(self):
        return
    def stop(self):
        Master.check = False
        return True

    def pause(self):
        Master.wait = True

    def unpause(self):
        Master.wait = False
