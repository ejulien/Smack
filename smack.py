# smack - Emmanuel Julien 2013 (ejulien@owloh.com)
# MIT Licensed

import api, copy

#
class context:
	def __init__(self, mods = None):
		self.ctx = {
			'workspace'		: None,
			'group'			: None,
			'project'		: None,
			'build'			: None,
			'target'		: None,
			'arch'			: None,
		}
		self.mod(mods)
		self.ctx_stack = []

	def __getitem__(self, name):
		return self.ctx[name]
	def __setitem__(self, name, value):
		self.ctx[name] = value

	def push(self):
		self.ctx_stack.append(copy.deepcopy(self.ctx))
	def pop(self):
		self.ctx = self.ctx_stack.pop()

	# does this context match another context
	def match(self, ctx, inherit = True):
		for key in self.ctx:
			if self.ctx[key] == '*':
				continue
			if key not in ctx:
				continue
			if (self.ctx[key] != ctx[key]):
				if self.ctx[key] != None and inherit == False:
					return False
				if self.ctx[key] != None and ctx[key] != None:
					return False
		return True

	# compare two context
	def compare(self, ctx):
		key_weights = ['workspace', 'group', 'project', 'build', 'target', 'arch']

		score = 0
		for key in self.ctx:
			if (key in ctx) and (key in key_weights):
				if (self.ctx[key] != None) and (self.ctx[key] == ctx[key]):
					score += key_weights.index(key) + 1

		return score

	# modify context
	def mod(self, mods):
		if mods != None:
			for k in mods.keys():
				self.ctx[k] = mods[k]
		return self

	# clone this context, optionally modify it
	def clone(self, mods = None):
		return copy.deepcopy(self).mod(mods)

	def formatFilter(self, key):
		return '-' if self.ctx[key] == None else self.ctx[key]

	def __repr__(self):
		return '[' + self.formatFilter('workspace') + '/' + self.formatFilter('group') + '/' + self.formatFilter('project') + '/' + self.formatFilter('build') + '/' + self.formatFilter('target') + '/' + self.formatFilter('arch') + ']'

	def set(self, workspace, group, project, build, target, arch):
		self.ctx['workspace'] = workspace
		self.ctx['group'] = group
		self.ctx['project'] = project
		self.ctx['build'] = build
		self.ctx['target'] = target
		self.ctx['arch'] = arch

#
class make:
	def __init__(self):
		self.config = {}
		self.ctx = context()

	def setWorkspace(self, name = None):
		self.ctx['workspace'] = name
	def setGroup(self, name = None):
		self.ctx['group'] = name
	def setProject(self, name = None):
		self.ctx['project'] = name
	def setBuild(self, name = None):
		self.ctx['build'] = name
	def setTarget(self, name = None):
		self.ctx['target'] = name
	def setArch(self, name = None):
		self.ctx['arch'] = name

	def push(self):
		self.ctx.push()
	def pop(self):
		self.ctx.pop()

	def getContext(self):
		return self.ctx

	# return the list of value of a configuration key for a given context
	def getConfigurationKeyValuesFilterByContext(self, key, filter_ctx, inherit = True):
		rval = []
		for config_list in self.config.values():
			for config in config_list:
				ctx = config['context']

				# check context match
				if not filter_ctx.match(ctx, inherit):
					continue

				if (ctx[key] != None) and (ctx[key] not in rval):
					rval.append(ctx[key])
		return rval

	# return the list of value of a configuration key
	def getConfigurationKeyValues(self, key):
		rval = []
		for config_list in self.config.values():
			for config in config_list:
				ctx = config['context']

				if key not in ctx:
					continue
				if (ctx[key] != None) and (ctx[key] not in rval):
					rval.append(ctx[key])
		return rval

	def setModContext(self, key, v, in_ctx):
		self.push()
		# apply input context changes
		for ck in in_ctx.keys():
			self.ctx[ck] = in_ctx[ck]
		self.set(key, v)
		self.pop()

	def getModContext(self, key, in_ctx):
		self.push()
		# apply input context changes
		for ck in in_ctx.keys():
			self.ctx[ck] = in_ctx[ck]
		r = self.get(key, self.ctx)
		self.pop()
		return r

	# set a key in the current context
	def set(self, key, v):
		if	key not in self.config:
			self.config[key] = []
		self.config[key].append({ 'value': v, 'context': copy.deepcopy(self.ctx.ctx) })

	# return a key value for the best match to a given context
	def getBestMatch(self, key, get_context):
		if key not in self.config:
			return None

		config_key_values = self.config[key]

		rval = None
		best_score = 0

		for value in config_key_values:
			score = get_context.compare(value['context'])

			if score > best_score:
				best_score = score
				rval = value['value']

		return rval

	def filterContext(self, v, f):
		if v == None:
			return True
		if f == '*':
			return True
		if f == None:
			return False	# NOTE shouldn't we pass if v is negated?

		exp_output = True
		if v.startswith('!'):
			v = v[1:]
			exp_output = not exp_output
		if f.startswith('!'):
			f = f[1:]
			exp_output = not exp_output
		return (v == f) == exp_output

	# return a key value for a given context (inherits unspecified values)
	def get(self, key, get_context = None):
		if get_context == None:
			get_context = self.ctx

		if key not in self.config:
			return None

		config_key_values = self.config[key]

		rval = None
		for value in config_key_values:
			value_context = value['context']

			mismatch = False
			for get_key in get_context.ctx.keys():
				if get_key in value_context:
					if not self.filterContext(value_context[get_key], get_context.ctx[get_key]):
						mismatch = True
						break

			if mismatch == False:
				rval = api.appendToList(rval, value['value'])

		return rval

	def getDefault(self, key, get_context, default):
		rval = self.get(key, get_context)

		if rval != None:
			return rval
		return default

	def getDependencies(self, ctx):
		deps = self.get('depends', ctx)
		if deps == None:
			return []

		out = []
		def insertDependency(ctx, prj, out):
			if prj in out:
				return out.index(prj)

			deps = self.get('depends', ctx.clone({'project': prj}))

			i = None
			if deps != None:
				for dep in deps:
					dep_i = insertDependency(ctx, dep, out)
					i = dep_i if i == None else min(dep_i, i)

			if i == None:
				i = 0

			out.insert(i, prj)
			return i

		# insert all dependencies
		for dep in deps:
			insertDependency(ctx, dep, out)

		return out

	def getLinksAcrossDependencies(self, deps, get_context = None):
		if get_context == None:
			get_context = self.ctx

		# deps are the base links
		out = copy.deepcopy(deps)

		# append explicit links for each dependency
		for dep in deps:
			links = self.get('link', get_context.clone({'project': dep}))
			if links != None:
				out = api.appendToList(out, [l for l in links if l not in out])

		# append context explicit links	
		links = self.get('link', get_context)
		if links != None:
			out = api.appendToList(out, [l for l in links if l not in out])

		return out

	# return a key value for a given context, collects values across all dependencies
	def getAcrossDependencies(self, deps, key, get_context = None):
		if get_context == None:
			get_context = self.ctx

		# gether across dependencies
		val = None
		for dep in deps:
			val = api.appendToList(val, self.get(key, get_context.clone({'project': dep})))

		# append context specific
		return api.appendToList(val, self.get(key, get_context))

	# test the presence of a value in a context's configuration key
	def testKeyForValue(self, key, val, get_context = None):
		if get_context == None:
			get_context = self.ctx

		rv = self.get(key, get_context)
		if rv == None:
			return False

		return val in rv if type(rv) == list else rv == val
#------------------
