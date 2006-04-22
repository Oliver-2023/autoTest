import os, pickle, tempfile
from autotest_utils import *
from error import *

class test:
	def __init__(self, job, testdir):
		self.job = job
		self.testdir = job.resultdir + '/' + testdir
		os.mkdir(self.testdir)
		self.resultsdir = self.testdir + "/results"
		os.mkdir(self.resultsdir)
		self.profdir = self.testdir + "/profiling"
		os.mkdir(self.profdir)
		self.debugdir = self.testdir + "/debug"
		os.mkdir(self.debugdir)
		self.tmpdir = self.testdir + "/tmp"
		os.mkdir(self.tmpdir)

	def __exec(self, parameters):
		sys.stdout.flush()
		sys.stderr.flush()
		pid = os.fork()
		if pid:			# parent
			(pid, status) = os.waitpid (pid,0)

			ename = self.testdir + "/debug/error-%d" % pid
			if (os.path.exists(ename)):
				fd = file(ename, 'r')
				err = pickle.load(fd)
				fd.close()

				raise err

			if (status != 0):
				raise TestError("test %s failed rc=%d" % (
					self.__class__.__name__, status))

		else:			# child
			try:
				try:
					os.chdir(self.testdir)
					self.setup()
					self.execute(*parameters)

				except AutotestError:
					raise

				except:
					raise UnhandledError('running test ' + \
						self.__class__.__name__ + "\n")

			except Exception, detail:
				ename = self.testdir + "/debug/error-%d" % (
					os.getpid())
				pickle.dump(detail, open(ename, "w"))
				sys.exit(1)

			sys.exit(0)

##	def __exec(self, parameters):
##		try:
##			os.chdir(self.testdir)
##			self.setup()
##			self.execute(*parameters)
##		except AutotestError:
##			raise
##		except:
##			raise UnhandledError('running test ' + \
##				self.__class__.__name__ + "\n")

	def setup(self):
		pass

	def run(self, testname, parameters):
		status = self.testdir + "/status"
		try:
			self.__exec(parameters)
		except Exception, detail:
			fd = file(status, "w")
			fd.write("FAIL " + detail.__str__() + "\n")
			fd.close()

			raise
		else:
			fd = file(status, "w")
			fd.write("GOOD Completed Successfully\n")
			fd.close()
