#
# MultiVeStA-Maude
#

import os
import random
import sys

from py4j.java_gateway import JavaGateway, GatewayParameters, CallbackServerParameters
import maude


def fatal_error(message):
	"""Issue a fatal error and terminate the simulator"""

	print(f'\x1b[31m{message}\x1b[0m', file=sys.stderr)

	# sys.exit(0) puts the MultiVeSta in a blocked state, so we send a signal
	# to the parent process to terminate its execution
	import signal
	os.kill(os.getppid(), signal.SIGTERM)


def collect_vars(term, varset):
	"""Find a variable in the term"""

	for arg in term.arguments():
		if arg.isVariable():
			varset.add(arg)
		else:
			collect_vars(arg, varset)


def parse_hole_term(module, term_str):
	"""Parse a term with a single variable"""

	term = module.parseTerm(term_str)

	if term is None:
		return None, None

	# Collect all variables in the term
	varset = set()
	collect_vars(term, varset)

	if len(varset) > 1:
		print(f'\x1b[33mWarning (simulator): the observation "{message}"'
		      'contains more than one variable.\x1b[0m')

	elif not varset:
		return term, None

	# We do not check whether the variable is in the appropriate kind
	return term, varset.pop()


class BaseSimulator:
	"""Base class for all Maude-based simulators"""

	class Java:
		implements = ['vesta.python.IPythonSimulatorWrapper']

	def __init__(self, initial):
		self.initial = initial
		self.module = initial.symbol().getModule()
		self.state = self.initial

		self.time = 0

		self.bool_sort = self.module.findSort('Bool')
		self.true = self.module.parseTerm('true', self.bool_sort.kind())

		self.obs_cache = {}  # Cache of parsed observations

	def setSimulatorForNewSimulation(self, random_seed):
		"""Restart simulator"""

		self.state = self.initial
		self.time = 0

	def performWholeSimulation(self):
		"""Perform a complete simulation (until a normal form)"""

		initial_time = -1

		while initial_time < self.time:
			initial_time = self.time
			self.performOneStepOfSimulation()

	def getTime(self):
		"""Get simulation time (number of steps)"""

		return float(self.time)

	def rval(self, observation):
		"""Evaluate observation on the current state of the simulation"""

		t, var = self.obs_cache.get(observation, (None, None))
		if not t:
			t, var = parse_hole_term(self.module, observation)
			self.obs_cache[observation] = (t, var)
		subs = maude.Substitution({var: self.state})
		t = subs.instantiate(t)
		t.reduce()

		return float(t == self.true) if t.getSort() == self.bool_sort else float(t)


class StrategyStepSimulator(BaseSimulator):
	"""Simulator where a strategy is the step"""

	def __init__(self, initial, strategy):
		super().__init__(initial)

		self.strategy = strategy

	def setSimulatorForNewSimulation(self, random_seed):
		"""Restart simulator and set the random seed"""

		super().setSimulatorForNewSimulation(random_seed)
		maude.setRandomSeed(random_seed)

	def performOneStepOfSimulation(self):
		"""Perform a step of the simulation"""

		next_state, _ = next(self.state.srewrite(self.strategy), (None, None))

		if next_state is not None:
			self.state = next_state
			self.time  += 1

	def performWholeSimulation(self):
		"""Perform a complete simulation (until a normal form)"""

		next_state, _ = next(self.state.srewrite(self.strategy), (None, None))

		while next_state is not None:
			self.state = next_state
			self.time += 1
			next_state, _ = next(self.state.srewrite(self.strategy), (None, None))


def all_children(graph, state):
	"""All children of a state in a graph"""

	children, next_state, index = [], graph.getNextState(state, 0), 0

	while next_state != -1:
		children.append(next_state)
		index += 1
		next_state = graph.getNextState(state, index)

	return children


class UmaudemcSimulator(BaseSimulator):
	"""Simulator that uses the probability assigners of umaudemc"""

	def __init__(self, initial, strategy=None, assigner='uniform', opaque=()):
		super().__init__(initial)

		import umaudemc.probabilistic as pb
		self.state_nr = 0

		if strategy:
			self.graph = pb.maude.StrategyRewriteGraph(initial, strategy, opaque)
		else:
			self.graph = pb.maude.RewriteGraph(initial)

		self.graph.strategyControlled = strategy is not None

		self.assigner, _ = pb.get_assigner(initial.symbol().getModule(), assigner)

	def setSimulatorForNewSimulation(self, random_seed):
		"""Restart simulator"""

		super().setSimulatorForNewSimulation(random_seed)
		self.state_nr = 0

	def performOneStepOfSimulation(self):
		"""Perform a step of the simulation"""

		solutions, index = [], 0

		successors = all_children(self.graph, self.state_nr)

		if successors:
			probs = self.assigner(self.graph, self.state_nr, successors)
			self.state_nr, = random.choices(successors, probs)
			self.state = self.graph.getStateTerm(self.state_nr)
			self.time += 1


class StrategyPathSimulator(BaseSimulator):
	"""Simulator based on the strategy where steps are rewrites"""

	def __init__(self, module, initial, strategy=None, assigner='uniform'):
		super().__init__(initial)

		from random_runner import RandomRunner
		from umaudemc.pyslang import StratCompiler

		ml = maude.getModule('META-LEVEL')
		sc = StratCompiler(module, ml, use_notify=True, ignore_one=True)
		p = sc.compile(ml.upStrategy(strategy))

		self.runner = RandomRunner(p, t)

	def setSimulatorForNewSimulation(self, random_seed):
		"""Restart simulator"""

		super().setSimulatorForNewSimulation(random_seed)
		self.runner.reset(self.initial)

	def performOneStepOfSimulation(self):
		"""Perform a step of the simulation"""

		next_state = self.runner.run()

		if next_state:
			self.state = next_state
			self.time += 1


class StrategyDTMCSimulator(BaseSimulator):
	"""Simulator based on the strategy where steps are rewrites"""

	def __init__(self, module, initial, strategy=None, assigner='uniform'):
		super().__init__(initial)

		from random_runner import RandomRunner
		from umaudemc.pyslang import StratCompiler, MarkovRunner, BadProbStrategy

		ml = maude.getModule('META-LEVEL')
		sc = StratCompiler(module, ml, use_notify=True, ignore_one=True)
		p = sc.compile(ml.upStrategy(strategy))

		try:
			self.graph = MarkovRunner(p, initial).run()
			self.node = self.graph

		except BadProbStrategy as bps:
			fatal_error(bps)

	def setSimulatorForNewSimulation(self, random_seed):
		"""Restart simulator"""

		super().setSimulatorForNewSimulation(random_seed)
		self.node = self.graph

	def performOneStepOfSimulation(self):
		"""Perform a step of the simulation"""

		nd_opts, qt_opts = len(self.node.children), len(self.node.child_choices)

		if nd_opts + qt_opts > 1:
			print('\x1b[33mUnquantified nondeterministic choices are present in the strategy.\x1b[0m')

		if nd_opts:
			next_node, *_ = self.node.children

		elif qt_opts:
			choice, *_ = self.node.child_choices
			next_node = random.choices(list(choice.keys()), choice.values())[0]

		if next_node:
			self.node = next_node
			self.state = self.node.term
			self.time += 1


def getenv_required(name):
	"""Get the value of an environment variable and terminate if it does not exists"""

	value = os.getenv(name)

	if value is None:
		fatal_error(f'Error (simulator): missing required {name} environment variable.')

	return value


if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='MultiVeSta interface to the Maude strategy language')

	parser.add_argument('port', help='Port for the connection with Java', type=int)
	parser.add_argument('cb_port', help='Port for the callback connection', type=int)

	args = parser.parse_args()

	print(f'Python engine: expecting connection with java on port: {args.port} and callback connection on port {args.cb_port}.')
	gateway = JavaGateway(start_callback_server=True, 
	                      gateway_parameters=GatewayParameters(port=args.port),
	                      callback_server_parameters=CallbackServerParameters(port=args.cb_port))

	maude.init()

	# The initial data of the problem has to be passed as environment variables
	maude_file = getenv_required('MTVMD_FILE')
	module_name = os.getenv('MTVMD_MODULE')
	metamodule_text = os.getenv('MTVMD_METAMODULE')
	initial_text = getenv_required('MTVMD_INITIAL')
	strategy_text = getenv_required('MTVMD_STRATEGY')
	method_text = getenv_required('MTVMD_METHOD')
	opaque_text = os.getenv('MTVMD_OPAQUE')

	maude.load(maude_file)
	m = maude.getCurrentModule() if module_name is None else maude.getModule(module_name)

	opaque = opaque_text.split(',') if opaque_text else ()

	if m is None:
		fatal_error(f'Error (simulator): no such module "{module_name}" exists.')

	if metamodule_text is not None:
		mt = m.parseTerm(metamodule_text)
		m = mt.downModule()

	if m is None:
		fatal_error(f'Error (simulator): cannot use "{module_text}" metamodule.')

	t = m.parseTerm(initial_text)

	if t is None:
		fatal_error(f'Error (simulator): cannot parse term "{initial_text}".')

	if strategy_text:
		s = m.parseStrategy(strategy_text)

		if s is None:
			fatal_error(f'Error (simulator): cannot parse strategy "{strategy_text}".')
	else:
		s = None

	# Select the simulator depending on the arguments

	if method_text == 'step':
		simulator = StrategyStepSimulator(t, s)

	elif method_text == 'strategy':
		simulator = StrategyPathSimulator(m, t, s)

	elif method_text == 'strategy-full':
		simulator = StrategyDTMCSimulator(m, t, s)

	else:
		simulator = UmaudemcSimulator(t, s, method_text, opaque=opaque)

	gateway.entry_point.playWithState(simulator)
