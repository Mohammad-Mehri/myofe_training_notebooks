# @Author: charlesmann
# @Date:   2022-07-13

import dolfin

class BoundaryConditions():

    def __init__(self, mesh_object):

        """ Initializes boundary conditions and could potentially alter them
        mid-simulation.

        inputs:
            :mesh_object: instance of class MeshData, used in calls to dolfin.DirichletBC()
            and marking facets of the mesh

        attributes:
            :dirichlet_bcs: python list of dolfin.DirichletBC objects
            :mesh_object: storing the passed in mesh object as an attribute
            :facets: facetboundaries mesh function to identify the facets
            :bc_expressions: dict of dolfin Expressions used to create time varying bcs

        methods:
            :assign_facets: Populate the facets list depending on geometry
            :unit_cube_uniaxial_stretch: assign Dirichlet boundary conditions to
            achieve uniaxial stretch
            ... (more can be added as needed)
        """

        self.dirichlet_bcs = []
        self.mesh_object = mesh_object
        self.bc_expressions = {}

        self.facets = self.assign_facets()



        return

    def assign_facets(self):

        """ Populate the facets attribute with facet ids dependent upon mesh
        geometry.

        inputs:
            :self: this BoundaryConditions instance, so all attributes are accessible
        """

        # Unit cube facets
        if self.mesh_object.geometry == "unit_cube":
            
            facetboundaries = self.mesh_object.facetboundaries

            # Set up classes to identify points on facets.

            # Let's go ahead and identify all six faces, as well as
            # a point at the origin to fix.

            # Names based on the assumption that the origin is bottom back Left
            # of the cube, with e1 pointing right, e2 pointing up, and e3 coming
            # out of the screen.

            class Left(dolfin.SubDomain):
                def inside(self, x, on_boundary):
                    tol = 1E-14
                    return on_boundary and abs(x[0]) < tol

            class Lower(dolfin.SubDomain):
                def inside(self, x, on_boundary):
                    tol = 1E-14
                    return on_boundary and abs(x[1]) < tol

            class Back(dolfin.SubDomain):
                def inside(self, x, on_boundary):
                    tol = 1E-14
                    return on_boundary and abs(x[2]) < tol

            class Front(dolfin.SubDomain):
                def inside(self, x, on_boundary):
                    tol = 1E-14
                    return on_boundary and abs(x[2] - 1.0) < tol

            class Top(dolfin.SubDomain):
                def inside(self, x, on_boundary):
                    tol = 1E-14
                    return on_boundary and abs(x[1] - 1.0) < tol

            class Right(dolfin.SubDomain):
                def inside(self, x, on_boundary):
                    tol = 1E-14
                    return on_boundary and abs(x[0] - 1.0) < tol

            class Fix(dolfin.SubDomain):
                def inside(self, x, on_boundary):
                    tol = 1E-14
                    return (dolfin.near(x[0],0.0,tol) and dolfin.near(x[1],0.0,tol) and dolfin.near(x[2],0.0,tol))

            # Create instances of the above classes
            left  = Left()
            lower = Lower()
            back  = Back()
            front = Front()
            top   = Top()
            right = Right()
            fix   = Fix()

            # Mark the facets
            # (don't think the class instances are needed after this, just
            # the facetboundaries mesh function)
            left.mark(facetboundaries, 1)
            lower.mark(facetboundaries, 2)
            back.mark(facetboundaries, 3)
            front.mark(facetboundaries, 4)
            top.mark(facetboundaries, 5)
            right.mark(facetboundaries, 6)
            fix.mark(facetboundaries, 7)

            # Now populate the facets list (also including the fix point)
            self.mesh_object.facetboundaries = facetboundaries
            self.facets = facetboundaries # now this instance and the mesh_object should reference same MeshFunction

            return

    def unit_cube_uniaxial_stretch(self, W):

        """ Populates the attribute "dirichlet_bcs" list to achieve uniaxial stretch.
        Assuming the preferred stretch direction is the x-direction, this could
        be generalized to accept a stretch direction. Also, if building a general
        framework, there are some ways to specify a function name in the instruction
        file, so a user could potentially list the desired boundary condition
        function there so this could be general.

        inputs:
            :self: this BoundaryConditions instance, so all attributes are accessible
            :W: doflin FunctionSpace. We need to know what we are constraining.
            For example to constrain displacement, we are constraining the first
            subspace of W W.sub(0) (remember, W is a mixed function space, consisting
            of a VectorFunctionSpace to hold the displacement solution, and a scalar
            FunctionSpace to hold the hydrostatic pressure solution)
        """

        # Get the facetboundaries MeshFunction
        facetboundaries = self.mesh_object.facetboundaries

        # Constrain left face in x (the 0th subspace of the VectorFunctionSpace)
        bc_left  = dolfin.DirichletBC(W.sub(0).sub(0), dolfin.Constant((0.0)), facetboundaries, 1)

        # Constrain lower face in z
        bc_lower = dolfin.DirichletBC(W.sub(0).sub(1), dolfin.Constant((0.0)), facetboundaries, 2)
        
        bc_back = dolfin.DirichletBC(W.sub(0).sub(2), dolfin.Constant((0.0)), facetboundaries, 3) # these three together should fix the origin

        # Fixing point at origin to prevent rigid body translation
        #bc_fix   = dolfin.DirichletBC(W.sub(0), dolfin.Constant((0.0, 0.0, 0.0)), fix, method="pointwise")
        #bc_fix   = dolfin.DirichletBC(W.sub(0), dolfin.Constant((0.0, 0.0, 0.0)), facetboundaries, 7, method="pointwise")

        # Expression used to control the right face displacement
        right_displacement = dolfin.Expression(("ud_x"), ud_x = 0.0, degree = 0)
        self.bc_expressions["right_displacement"] = right_displacement
        bc_right= dolfin.DirichletBC(W.sub(0).sub(0), right_displacement, facetboundaries, 6)

        self.dirichlet_bcs = [bc_left, bc_lower, bc_back, bc_right]

        return
