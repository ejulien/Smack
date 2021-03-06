# smack - Emmanuel Julien 2013 (ejulien@owloh.com)
# MIT Licensed

import os, copy, fnmatch

__all__ = ["Print"]
try:
  Print = eval("print")
except SyntaxError:
  try:
    D = dict()
    exec("from __future__ import print_function\np=print", D)
    Print = D["p"]
    del D
  except SyntaxError:
    del D
    def Print(*args, **kwd):
      fout = kwd.get("file", sys.stdout)
      w = fout.write
      if args:
        w(str(args[0]))
        sep = kwd.get("sep", " ")
        for a in args[1:]:
          w(sep)
          w(str(a))
      w(kwd.get("end", "\n"))

#------------------------------------------------------------------------------
class hookCallable:
	def __init__(self, func, over):
		self.base = func
		self.over = over
	def __call__(self, *args):
		return self.over(self.base, *args)

def hook(func, over):
	return hookCallable(func, over)
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def fileWriteStringList(f, list, sep = ','):
	first = True
	for i in list:
		if first == False:
			f.write(sep + ' ')
		f.write("'" + i + "'")
		first = False
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def getFileExt(name):
	return os.path.splitext(name)[1]
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def translate(flags, dict, default):
	if flags == None:
		return default
	for key in dict.keys():
		if key in flags:
			return dict[key]
	return default
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def substractLists(a, b):	# a project_defines
	if a == None:
		return []
	if b != None:
		return [v for v in a if v not in b]
	return a

def appendToList(var, value):
	if value == None:
		return var

	if (type(value).__name__ == 'inputs') or ((type(value).__name__ == 'instance') and (value.__class__.__name__ == 'inputs')):
		value = value.getList()

	if	var == None:
		var = copy.deepcopy(value)
		if	type(var) != list:
			var = [var]
	else:
		if	type(value) == list:
			for v in value:
				if v not in var:
					var.append(v)
		else:
			if value not in var:
				var.append(value)
	return var
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def log(msg, indent_level = 0):
	out = ''
	for i in range(0, indent_level):
		out += '\t'
	Print( out + msg )

def warning(msg, indent_level = 0):
	out = ''
	for i in range(0, indent_level):
		out += '\t'
	Print( out + '[Warning] ' + msg )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def normPathForOs(path, convention = 'unix'):
	os_separator = '\\' if convention == 'windows' else '/'
	norm = os.path.normpath(path)
	if os.sep != os_separator:
		norm = norm.replace(os.sep, os_separator)
	return norm

def getRelativePath(path, ref_path, convention = 'unix'):
	if path.find('$(') == 0:
		return path
	if os.path.isabs(path) == False:
		path = os.path.abspath(path)
	if os.path.isabs(ref_path) == False:
		ref_path = os.path.abspath(ref_path)
	try:
		return normPathForOs(os.path.relpath(path, ref_path), convention)
	except:
		return path
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
class inputs:
	def __init__(self):
		self.clear()

	def getList(self):
		return self.list

	def clear(self):
		self.list = []

	def getInputs(self, path, pattern, recursive = True):
		inputs = []
		for (dirpath, dirname, filenames) in os.walk(path):

			for (filename) in filenames:
				if	type(pattern) == list:
					for (p) in pattern:
						if fnmatch.fnmatch(filename, p):
							inputs.append(os.path.normpath(os.path.join(dirpath, filename)))
							break
				else:
					if fnmatch.fnmatch(filename, pattern):
						inputs.append(os.path.normpath(os.path.join(dirpath, filename)))

			if	(recursive == False):
				break
		return inputs

	def excludeFile(self, files):
		if type(files) != list:
			files = [files]

		files = [os.path.normpath(f) for f in files]

		self.list = [f for f in self.list if f not in files]
		return self

	def addFile(self, files):
		if type(files) != list:
			files = [files]
		self.list.extend(files)
		return self

	def add(self, path, pattern, recursive = True):
		if type(path) != list:
			path = [path]

		for p in path:
			inputs = self.getInputs(p, pattern, recursive)
			for input in inputs:
				self.list.append(input)
		return self

	def exclude(self, path, pattern, recursive = True):
		if type(path) != list:
			path = [path]

		for p in path:
			excludes = self.getInputs(p, pattern, recursive)
			self.list = list(set(self.list) - set(excludes))	# substract and sort
		return self
#------------------------------------------------------------------------------
