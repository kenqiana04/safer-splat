"""Read-only audit of Nerfstudio 1.1.5 Splatfacto loss behavior.

The server audit inspects get_loss_dict and runtime metadata without calling an
optimizer.  V1R6's stock objective is RGB photometric loss; GT depth is not a
loss input.
"""
