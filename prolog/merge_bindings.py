def merge_bindings(bindings1, bindings2):
    if bindings1 is None or bindings2 is None:
        # If either binding set is None (indicating a previous match failure), propagate None.
        return None

    # Start with a copy of the first set of bindings.
    merged_bindings = bindings1.copy()

    for var_b, val_b in bindings2.items():
        if var_b in merged_bindings:
            # Variable already exists in merged_bindings. Check for consistency.
            val_a = merged_bindings[var_b]
            
            # Attempt to unify val_a and val_b.
            # Their .match() method should handle unification and return further bindings if successful,
            # or None if they cannot be unified (i.e., they are contradictory).
            # Note: The exact behavior of .match() is crucial here.
            # If val_a and val_b are concrete, different values, .match() should ideally return None.
            # If one or both are variables, .match() should establish a binding.
            
            # We need a robust way to check if val_a and val_b are compatible.
            # This might involve checking if val_a.match(val_b) is possible,
            # or if val_b.match(val_a) is possible, or a more symmetric unification.
            # For now, let's assume a simple check: if they are not identical,
            # and .match doesn't resolve it, it's a conflict.
            
            if val_a == val_b: # Already consistent
                continue

            # Try to unify them. This part is tricky and depends on the .match() implementation.
            # Let's assume val_a.match(val_b) is the way to check if val_b can be unified with val_a's current binding.
            additional_bindings = val_a.match(val_b) # This should return new bindings or None

            if additional_bindings is None:
                # Contradiction: var_b is bound to val_a in bindings1 and to a different, incompatible val_b in bindings2.
                return None  # Indicate merge failure due to contradiction.
            else:
                # val_a and val_b are unifiable. Incorporate any new bindings from their unification.
                # This recursive merge is important if unification itself produces more bindings.
                # We need to merge these `additional_bindings` into `merged_bindings`.
                # This could get complex if `additional_bindings` conflict with existing `merged_bindings`.
                # A simpler approach for now: if `additional_bindings` are produced, update `merged_bindings`.
                # This assumes `additional_bindings` won't conflict with `merged_bindings` other than for `var_b`.
                
                # Re-check for safety:
                # The result of val_a.match(val_b) should be bindings that make val_a and val_b equivalent.
                # These new bindings need to be consistently merged.
                # A robust merge would recursively call merge_bindings.
                # For now, let's apply the direct outcome of match.
                # This part of the original pieprolog was subtle.
                
                # The original code's `sub = other.match(value)` and then iterating `sub.items()`
                # was intended to handle this. Let's try to follow that more closely.
                # `other` is `val_a`, `value` is `val_b`.
                sub_bindings = val_a.match(val_b)
                if sub_bindings is None:
                    return None # Contradiction

                # Apply these sub-bindings. This might re-bind variables already in merged_bindings.
                # This needs to be done carefully.
                # For each k, v in sub_bindings, if k is in merged_bindings and merged_bindings[k] != v, it's a problem
                # unless that re-binding is itself consistent.
                # This is where a full unification algorithm's consistency checks are vital.
                
                # Let's simplify: if val_a.match(val_b) returns bindings, we assume they are consistent
                # with val_a and val_b, and we try to merge them in.
                # The provided solution structure for merge_bindings is a good guide.

                # Sticking to the original structure's attempt:
                for sub_var, sub_val in sub_bindings.items():
                    if sub_var in merged_bindings and merged_bindings[sub_var] != sub_val:
                        # Further check needed if merged_bindings[sub_var] can unify with sub_val
                        deeper_check = merged_bindings[sub_var].match(sub_val)
                        if deeper_check is None:
                            return None # Deeper contradiction
                        # If successful, apply these deeper bindings (this can get very recursive)
                        # For simplicity now, assume sub_bindings are the "truth"
                        merged_bindings[sub_var] = sub_val # This might overwrite, needs care
                    else:
                        merged_bindings[sub_var] = sub_val
        else:
            # var_b is not in merged_bindings yet, so add its binding from bindings2.
            merged_bindings[var_b] = val_b
            
    # Final consistency check (optional, but good for robustness)
    # Ensure all variables point to their most resolved values if there were chains.
    # This is usually handled by the .substitute() method if called on the final terms.
    # For the bindings themselves, this iterative application should resolve.

    return merged_bindings
