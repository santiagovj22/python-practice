from viztracer import VizTracer
tracer = VizTracer() #global tracer object

# VizTracer is a debugging/profiling tool it can display every function executed and the corresponding entry/exit time 
# VizTracer will create a html or json file than can be viewed in browser
# Usage: put '@decorator_viztracer' in front of the function that you want to profile

def decorator_viztracer(orig_func):
    def wrapper(*args,**kwargs):
        from viztracer import get_tracer
        tracer = get_tracer()
        tracer.start()
        result = orig_func(*args,**kwargs)
        tracer.stop()
        tracer.save('{}.html'.format(orig_func.__name__))  
        return result
    return wrapper