# @Author: charlesmann
# @Date:   2022-07-13

import dolfin

class MeshObject():
    
    def __init__(self,geometry):
        
        """ Create/import a mesh object.
        
        inputs: 
            :geometry: string specifying desired dolfin geometry
            
        attributes:
            :geometry: string, same as geometry
            :facetboundaries: dolfin MeshFunction to mark facets
            :N: FacetNormals of mesh (don't recall off top of my head if used for LV)
            :mesh: dolfin mesh object
            :dx: 
            ...
        """
        
        self.geometry = geometry
        
        # Create mesh object based on string.
        # To generalize, this could be a string for a dolfin mesh, or a path to a mesh to import
        # With each dolfin mesh type (unit cube, unit square, boxmesh, etc.) there are variable
        # inputs they accept. Since we aren't building in a lot of generality here, just 
        # going to hard code the UnitCubeMesh resolution
        if geometry == "unit_cube":
            
            self.mesh = dolfin.UnitCubeMesh(1,1,1)
            
        self.facetboundaries = dolfin.MeshFunction('size_t', self.mesh, self.mesh.topology().dim()-1)
        self.facetboundaries.set_all(0)

        self.N  = dolfin.FacetNormal(self.mesh)
        # integration measures
        self.dx = dolfin.dx(self.mesh,metadata = {"integration_order":2})
        self.ds = dolfin.ds(subdomain_data = self.facetboundaries)
        
        return