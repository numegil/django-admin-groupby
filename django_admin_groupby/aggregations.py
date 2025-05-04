class PostProcess:
    """
    A class representing a post-process aggregation operation.
    
    This provides a consistent API with Django's built-in aggregation classes.
    
    Args:
        func: A callable that takes a model instance and returns a value to aggregate
        verbose_name: A human-readable name for the aggregation
        aggregate: The type of aggregation to perform (sum, avg, min, max, count)
    """
    
    def __init__(self, func, verbose_name=None, aggregate="sum"):
        assert callable(func), "The 'func' parameter must be callable"
        self.func = func
        self.aggregate = aggregate
        self.extra = {'verbose_name': verbose_name} if verbose_name else {}
        
    def __repr__(self):
        return f"PostProcess({self.func.__name__ if hasattr(self.func, '__name__') else 'lambda'}, aggregate={self.aggregate})"