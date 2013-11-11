
import re
import sys

defines = {}
cdefs = []

location_re = re.compile(r'^# \d+ "([^"]*)"')
glpath_re = re.compile(r'^(?:.*[\\/]|\A)(gl|glu|glfw3|glext)\.h$')
define_re = re.compile(r"^#define\s+([^\s]+)\s+([^\s]+)$")

number_re = re.compile(r"^-?[0-9]+$")
hex_re = re.compile(r"0x[0-9a-fA-F]+$")

# Set of known #defines that we don't need to include
INVALID_DEFINES = set(["GLAPI", "APIENTRY", "GLU_TESS_MAX_COORD", "gluErrorStringWIN", "WINGDIAPI", "CALLBACK"])

if __name__ == "__main__":
	in_gl = False
	for line in sys.stdin:
		# Ignore blank lines
		line = line.strip()
		if not line:
			continue
		
		# Is this a preprocessor statement?
		if line.startswith("#"):
			
			# Is this a location pragma?
			location_match = location_re.match(line)
			if location_match:
				# If we are transitioning to a header we need to parse, set the flag
				glpath_match = glpath_re.match(location_match.group(1))
				in_gl = bool(glpath_match)
				continue
			
			if in_gl:
				# Is it a define?
				define_match = define_re.match(line)
				if define_match:
					name, val = define_match.groups()
					
					if val in defines:
						# Is this an alias of something we have already defined?
						val = defines[val]
					elif number_re.match(val) or hex_re.match(val):
						# Is this a number?
						# Store the define
						defines[name] = val
					elif val == "0xFFFFFFFFFFFFFFFFull":
						# Fix for GL_TIMEOUT_IGNORED
						defines[name] = val
					elif val == "0xFFFFFFFFu":
						# Fix for GL_INVALID_INDEX
						defines[name] = "0xFFFFFFFF"
					elif name not in INVALID_DEFINES:
						# Incompatible define
						print("Invalid define:", name, file=sys.stderr)
					
					continue
		
		# Otherwise just include it in the cdef
		elif in_gl:
			# Windows likes to add __stdcall__ to everything, but it isn't needed and is actually harmful when using under linux.
			line = line.replace('__attribute__((__stdcall__)) ', '')
			# While linux likes to add __attribute__((visibility("default"))) 
			line = line.replace('__attribute__((visibility("default"))) ', '')
			cdefs.append(line.replace('__attribute__((__stdcall__)) ', ''))
	
	# Output the file
	print("--[[ BEGIN AUTOGENERATED SEGMENT ]]")
	print("local glc; do require('ffi').cdef [[")
	for line in cdefs:
		print("\t", line, sep="")
	print("\t]]; glc = {")
	
	for k in sorted(defines.keys()):
		print("\t%s = %s," % ("['"+k+"']", defines[k]))
	
	print("} end")
	print("--[[ END AUTOGENERATED SEGMENT ]]")
