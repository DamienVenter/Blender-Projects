"""Which faces of a kit plastic show the kit, and which are its inner or back faces (decision 37 round 2).

build_bike.kit_materials gives a plastic's faces the kit's projections (side, top, plate) by where each face is and
which way it looks. The projections are painted in a view (the side view, the top view, the plate from the front), so
a face on the far side of the part's own shell took the same texels as the face in front of it: the right side
panel's inner skin showed a mirrored VENTER behind the shock in the photo-03 view (r7). Real kits are stuck on the
outside: inner and back faces are the bare plastic. Two kinds of part:

  shells (built with their thickness: side panels, shrouds, the number plate): a face is an inner face when the
      part's own skin lies just in front of it along the projection's view direction (within REACH, about the
      thickness) and runs parallel to it (normals within acos(PARALLEL)): the other skin of the same sheet, not a
      fold of the same skin seen over its edge. Normals are not trusted: the shells are not all wound outward.
  single surfaces (THIN in build_bike, solidified in Blender inward, against their normals): the surface itself is
      the outer skin where its normals look along the view direction; where they look away, the solidify shell on
      its other side is. Decided per connected surface (outward).

Pure numpy (no bpy, no scipy) so that tests can run it on the parts directly."""
import numpy as np

# kit material: (axis, sign) of the direction the projection looks FROM (its outside): x forward, y left, z up
AXIS = {"livery_L": (1, 1.0), "livery_R": (1, -1.0), "livery_fender": (2, 1.0), "fender_front": (2, 1.0),
        "livery_top": (2, 1.0), "plate": (0, 1.0)}
REACH = 0.006       # m: the other skin of a shell (plastics: 3 mm panels and shrouds, 1.5 mm walls, 4 mm plates)
EPS = 0.0002        # m: not the face itself (neighbours that share its edge)
PARALLEL = 0.8      # |n1 . n2|: the two skins of one sheet are parallel; a fold of one skin turns away


def normals(V, faces):
    """Unit normals by Newell's method (any polygon) and areas."""
    N = np.zeros((len(faces), 3))
    for k, f in enumerate(faces):
        p = V[list(f)]
        q = np.roll(p, -1, axis=0)
        N[k] = [((p[:, 1] - q[:, 1]) * (p[:, 2] + q[:, 2])).sum(), ((p[:, 2] - q[:, 2]) * (p[:, 0] + q[:, 0])).sum(),
                ((p[:, 0] - q[:, 0]) * (p[:, 1] + q[:, 1])).sum()]
    A = np.linalg.norm(N, axis=1)
    return N / np.maximum(A, 1e-30)[:, None], A / 2


def covered(V, faces, sel, axis, sgn, reach=REACH, cell=0.004):
    """For each face index in sel: is another skin of the same shell just in front of it along sgn * axis?"""
    V = np.asarray(V, float)
    N, _ = normals(V, faces)
    a, b = [i for i in range(3) if i != axis]
    T, own = [], []
    for k, f in enumerate(faces):
        for i in range(1, len(f) - 1):
            T.append((f[0], f[i], f[i + 1]))
            own.append(k)
    T, own = np.asarray(T), np.asarray(own)
    P, D = V[:, [a, b]], V[:, axis] * sgn
    lo = P.min(0)
    c0 = np.floor((P[T].min(1) - lo) / cell).astype(int)
    c1 = np.floor((P[T].max(1) - lo) / cell).astype(int)
    nx = int(c1[:, 0].max()) + 2
    keys, tris = [], []
    for t in range(len(T)):                                         # each triangle in every cell its box touches
        i, j = np.meshgrid(np.arange(c0[t, 0], c1[t, 0] + 1), np.arange(c0[t, 1], c1[t, 1] + 1))
        keys.append((i * nx + j).ravel())
        tris.append(np.full(i.size, t))
    keys, tris = np.concatenate(keys), np.concatenate(tris)
    o = np.argsort(keys, kind="stable")
    keys, tris = keys[o], tris[o]
    out = np.zeros(len(sel), bool)
    for q, k in enumerate(sel):
        f = list(faces[k])
        c, cd = P[f].mean(0), D[f].mean()
        ci = np.floor((c - lo) / cell).astype(int)
        key = ci[0] * nx + ci[1]
        cand = tris[np.searchsorted(keys, key):np.searchsorted(keys, key, side="right")]
        cand = cand[(own[cand] != k) & (np.abs(N[own[cand]] @ N[k]) > PARALLEL)]
        if not len(cand):
            continue
        A_, B_, C_ = P[T[cand, 0]], P[T[cand, 1]], P[T[cand, 2]]
        e1, e2, r = B_ - A_, C_ - A_, c - A_
        det = e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]
        ok = np.abs(det) > 1e-14
        det = np.where(ok, det, 1.0)
        u = (r[:, 0] * e2[:, 1] - r[:, 1] * e2[:, 0]) / det
        v = (e1[:, 0] * r[:, 1] - e1[:, 1] * r[:, 0]) / det
        inside = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
        dep = D[T[cand, 0]] * (1 - u - v) + D[T[cand, 1]] * u + D[T[cand, 2]] * v
        dz = dep - cd
        out[q] = bool(np.any(inside & (dz > EPS) & (dz < reach)))
    return out


def components(faces, sel):
    """Label the faces in sel by connected surface (faces that share a vertex)."""
    parent = list(range(len(sel)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    first = {}
    for q, k in enumerate(sel):
        for v in faces[k]:
            if v in first:
                a, b = root(q), root(first[v])
                if a != b:
                    parent[a] = b
            else:
                first[v] = q
    return np.array([root(q) for q in range(len(sel))])


def outward(V, faces, sel, axis, sgn):
    """For each face index in sel of a single surface: do its normals look out along sgn * axis? Decided per
    connected surface by the area-weighted majority of n . d: one surface is wound one way, and a surface wrapped
    round something (a fork guard round its tube) has faces that look along the axis both ways."""
    N, A = normals(np.asarray(V, float), faces)
    sel = list(sel)
    nd = N[sel, axis] * sgn * A[sel]
    lab = components(faces, sel)
    vote = {c: nd[lab == c].sum() for c in np.unique(lab)}
    return np.array([vote[c] >= 0 for c in lab])


def back_faces(V, faces, M, kit, thin):
    """M: each face's material name after the kit assignment, kit: the material it had before (its plain plastic).
    Returns (front, back): each face's material, and the material of its other side (single surfaces: the solidify
    shell's). Shells: covered kit faces go back to their plain plastic. Single surfaces: a kit face whose normal looks
    in keeps the kit on its back (the shell outside it) and the plain plastic on its front."""
    front, back = list(M), list(M)
    for mat, (axis, sgn) in AXIS.items():
        sel = [k for k, m in enumerate(M) if m == mat]
        if not sel:
            continue
        if thin:
            for k, out in zip(sel, outward(V, faces, sel, axis, sgn)):
                front[k], back[k] = (mat, kit[k]) if out else (kit[k], mat)
        else:
            for k, cov in zip(sel, covered(V, faces, sel, axis, sgn)):
                if cov:
                    front[k] = back[k] = kit[k]
    return front, back
