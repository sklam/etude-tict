# TICT

## A Transactional Dictionary

## Warning.  This is currently just a study.


- Implement `tict.Tict` with the `MutableMapping` interface.
- Implement `.save()` for marking a state that can be reverted to.
- Implement `.rollback(state)` for **removing** actions to the dictionary to recover to a previous state.  This operation is non-reversible.
- Implement `.revert(state)` to **undo** actions to the dictionary to recover the observable key-values at a previous state.  This operation is reversible.

