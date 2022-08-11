# @Author: charlesmann
# @Date:   2022-03-17T10:19:33+01:00
# @Last modified by:   charlesmann
# @Last modified time: 2022-03-25T13:28:16+01:00

# Different classes for initiating materials as cohorts
from importlib import import_module
import numpy as np
import math
import dolfin
import ufl
#import lifetime_functions

i, j = ufl.indices(2)

class GuccioneMaterial():

    def __init__(self, params, coordinate_system, F_t):
        
        """Initializes a instance of this material class to become a cohort of a
        constituent. Sets the cohort's initial reference local coordinate 
        system, pre-stretch tensor G, survival function, and initializes this 
        cohort's strain energy function.

        :params:  dictionary of material specific parameters
        :coordinate_system: list of vectors forming the basis for this cohort's 
                            local reference coordinate system
        :F_t: Body deformation gradient at time of this cohort's creation. 
              Between this and the pre-stretch tensor G, the reference 
              configuration for this cohort can be solved for
        """

        # Add check for parameters, if not use baseline parameters?
        # material parameters
        self.c   = params["c"][0]
        self.bf  = params["bf"][0]
        self.bfx = params["bfx"][0]
        self.bx  = params["bx"][0]
        mesh_object = params["mesh_object"][0]
        #self.phi = params["phi"][0]
        #mesh = params["mesh"][0]

        self.mesh = mesh_object.mesh

        #self.rho = dolfin.Function(dolfin.FunctionSpace(mesh,"DG",1))
        #try:
        #    temp = dolfin.project(params["rho"][0],dolfin.FunctionSpace(mesh,"DG",1))
        #    self.rho.assign(temp)
        #except:
        #    self.rho.vector()[:] = params["rho"][0]

        #survival_fcn_name = params["survival_fcn"][0]
        #met2 = getattr(lifetime_functions,survival_fcn_name)
        #self.survival_fcn = met2

        #self.survival_fcn_params = params["survival_fcn_params"]

        # local coordinate system
        # list of f0, s0, n0 functions for this material
        self.local_coordinate_system = coordinate_system
        E1 = self.local_coordinate_system[0]
        E2 = self.local_coordinate_system[1]
        E3 = self.local_coordinate_system[2]
        
        # Create tensors for local coordinate system
        self.M1 = dolfin.as_tensor(E1[i]*E1[j], (i, j))
        self.M2 = dolfin.as_tensor(E2[i]*E2[j], (i, j))
        self.M3 = dolfin.as_tensor(E3[i]*E3[j], (i, j))

        #self.G = params["G"][0]
        self.G = dolfin.Identity(3)

        # Deformation gradient at time of material deposition
        #self.F_cohort0 = dolfin.project(F_t,dolfin.TensorFunctionSpace(self.mesh,"DG",1)).copy()
        #self.E_cohort0 = 0.5*(self.F_cohort0.T*self.F_cohort0 - dolfin.Identity(3))
        self.F_cohort0 = F_t
        self.E_cohort0 = 0.5*(F_t.T*F_t - dolfin.Identity(3))
        #self.sef = self.initialize_strain_energy_function(self.F_cohort0, self.E_cohort0,0)
        self.sef = self.initialize_strain_energy_function(self.F_cohort0, self.E_cohort0,0)
        
        #self.constituent_phi = 1.0 #updated elsewhere for now
        #self.cauchy_stress_history = []
        #self.phi_history = []

    def initialize_strain_energy_function(self, F_body, E_body, cohort_count):

        
        """Initializes the strain energy function for this cohort. The strain 
        energy function depends on the elastic deformation, which is cohort 
        specific.

        :F_body: Body deformation gradient at time t
        :E_body: Green-Lagrange strain tensor calculated from F_body, doesn't 
                 need to be a separate argument
        :cohort_count: Used to determine whether this cohort is the first cohort
                       or not. The pre-stretch tensor needs to be the identity 
                       for initialization of the body.

        :return: W, a ufl product object representing the strain energy function
        """

        # F and E are given as for the entire body at some time t
        F_cohort = F_body*dolfin.inv(self.F_cohort0)*self.G
        F_cohort = F_body
        self.J_cohort = dolfin.det(F_cohort)
        # Hard coding I, assuming dimension 3
        I = dolfin.Identity(3)
        E_cohort = 0.5*(F_cohort.T*F_cohort - I)

        f0 = self.local_coordinate_system[0]
        s0 = self.local_coordinate_system[1]
        n0 = self.local_coordinate_system[2]

        c   = self.c
        bf  = self.bf
        bfx = self.bfx
        bx  = self.bx
        #phi = self.phi

        # Get local coordinate strain values
        Eff = dolfin.inner(f0, E_cohort*f0)
        Ess = dolfin.inner(s0, E_cohort*s0)
        Enn = dolfin.inner(n0, E_cohort*n0)
        Efs = dolfin.inner(f0, E_cohort*s0)
        Efn = dolfin.inner(f0, E_cohort*n0)
        Ens = dolfin.inner(n0, E_cohort*s0)
        Esf = dolfin.inner(s0, E_cohort*f0)
        Esn = dolfin.inner(s0, E_cohort*n0)
        Enf = dolfin.inner(n0, E_cohort*f0)

        # Explicitly define each term, don't rely on symmetry
        Q = bf*Eff**2.0 + bx*(Ess**2.0 + Enn**2.0 + Ens**2.0 + Esn**2.0) + bfx*(Efs**2.0 + Esf**2.0 + Efn**2.0 + Enf**2.0)

        W = (c/2.0)*(dolfin.exp(Q) - 1.0)
        self.sef = W

        return W


    def calculate_local_pk2_tensor_field(self, E_cohort):
        
        """Calculate this cohort's Second Piola-Kirchhoff Stress tensor field, 
        either to record or use as stimulus.
    
        :E_cohort: This cohort's Green-Lagrange strain tensor
    
        :return: S_local, a ufl tensor, the PK2 stress tensor with respect to 
                 the local coordinate system (not global!)
        """

        f0 = self.local_coordinate_system[0]
        s0 = self.local_coordinate_system[1]
        n0 = self.local_coordinate_system[2]

        c   = self.c
        bf  = self.bf
        bfx = self.bfx
        bx  = self.bx
        #phi = self.phi

        # Get local coordinate strain values
        Eff = dolfin.inner(f0, E_cohort*f0)
        Ess = dolfin.inner(s0, E_cohort*s0)
        Enn = dolfin.inner(n0, E_cohort*n0)
        Eff = dolfin.variable(dolfin.inner(f0, E_cohort*f0))
        Ess = dolfin.variable(dolfin.inner(s0, E_cohort*s0))
        Enn = dolfin.variable(dolfin.inner(n0, E_cohort*n0))
        Efs = dolfin.variable(dolfin.inner(f0, E_cohort*s0))
        Efn = dolfin.variable(dolfin.inner(f0, E_cohort*n0))
        Ens = dolfin.variable(dolfin.inner(n0, E_cohort*s0))
        Esf = dolfin.variable(dolfin.inner(s0, E_cohort*f0))
        Esn = dolfin.variable(dolfin.inner(s0, E_cohort*n0))
        Enf = dolfin.variable(dolfin.inner(n0, E_cohort*f0))

        Q = bf*(Eff**2.0) + bx*(Ess**2.0 + Enn**2.0 + Ens**2.0 + Esn**2.0) + bfx*(Efs**2.0 + Esf**2.0 + Efn**2.0 + Enf**2.0)

        W = (c/2.0)*(dolfin.exp(Q) - 1.0)

        # Differentiation W wrt to E
        S_local = (dolfin.diff(W,Eff)*dolfin.as_tensor(f0[i]*f0[j], (i,j)) + dolfin.diff(W,Efs)*dolfin.as_tensor(f0[i]*s0[j], (i,j)) 
                + dolfin.diff(W,Efn)*dolfin.as_tensor(f0[i]*n0[j], (i,j)) + dolfin.diff(W,Esf)*dolfin.as_tensor(s0[i]*f0[j], (i,j)) 
                + dolfin.diff(W,Ess)*dolfin.as_tensor(s0[i]*s0[j], (i,j)) + dolfin.diff(W,Esn)*dolfin.as_tensor(s0[i]*n0[j], (i,j)) 
                + dolfin.diff(W,Enf)*dolfin.as_tensor(n0[i]*f0[j], (i,j)) + dolfin.diff(W,Ens)*dolfin.as_tensor(n0[i]*s0[j], (i,j)) 
                + dolfin.diff(W,Enn)*dolfin.as_tensor(n0[i]*n0[j], (i,j)))
        
        return S_local

    def calculate_local_cauchy_stress_field(self, F_body):
        
        """Calculate the local cauchy stress tensor field by transforming the PK2 stress.
    
        :F_body: Deformation gradient of body
    
        :return: cauchy, a ufl tensor that is the cauchy stress with respect to 
                 current coordinate system, pk2 as above, cur_local_coords, a 
                 list of vectors representing the current coordinate system for 
                 this cohort
        """
    
        # F input is body deformation gradient. Need to calculate cohort specific
        F_cohort = F_body*dolfin.inv(self.F_cohort0)*self.G
        I = dolfin.Identity(3) # will this need to be identity in local coordinates?
        E_cohort = 0.5*(F_cohort.T*F_cohort - I)
        J_cohort = dolfin.det(F_cohort)

        f = F_cohort*self.local_coordinate_system[0]
        s = F_cohort*self.local_coordinate_system[1]
        n = F_cohort*self.local_coordinate_system[2]
        
        # Normalize current coordinate system
        f = f/dolfin.sqrt(dolfin.inner(f,f))
        s = s/dolfin.sqrt(dolfin.inner(s,s))
        n = n/dolfin.sqrt(dolfin.inner(n,n))

        cur_local_coords = [f, s, n]

        pk2 = self.calculate_local_pk2_tensor_field(E_cohort)
        cauchy = (1.0/J_cohort)*F_cohort*pk2*F_cohort.T

        return cauchy, pk2, cur_local_coords

    def calculate_survival_proportion(self):
        
        """Returns the factor that represents the proportion of this cohort 
        that is remaining as calculated by this cohort's specified survival function.
   
        :return: survival_proportion, a dolfin function because deposition and 
                 mass removal can vary spatially
       """
       
        survival_proportion = self.survival_fcn(self.survival_fcn_params)
        return survival_proportion

class FiberMaterial():

    def __init__(self, params, coordinate_system, F_t):
        
        """Initializes a instance of this material class to become a cohort of a
        constituent. Sets the cohort's initial reference local coordinate 
        system, pre-stretch tensor G, survival function, and initializes this 
        cohort's strain energy function.

        :params:  dictionary of material specific parameters
        :coordinate_system: list of vectors forming the basis for this cohort's 
                            local reference coordinate system
        :F_t: Body deformation gradient at time of this cohort's creation. 
              Between this and the pre-stretch tensor G, the reference 
              configuration for this cohort can be solved for
        """

        # Material parameters
        self.c1   = params["c1"][0]
        self.c2  = params["c2"][0]
        self.phi = params["phi"][0]
        self.mesh = params["mesh"][0]
        mesh = self.mesh

        # Initial mass density function
        self.rho = dolfin.Function(dolfin.FunctionSpace(mesh,"DG",1))
        try:
            # if adding a new cohort of material based on stimulus
            temp = dolfin.project(params["rho"][0],dolfin.FunctionSpace(mesh,"DG",1))
            self.rho.assign(temp)
        except:
            # first cohort of this constituent, initialize to uniform  density
            self.rho.vector()[:] = params["rho"][0]

        # Each cohort of a constituent needs its own survival function
        survival_fcn_name = params["survival_fcn"][0]
        met2 = getattr(lifetime_functions,survival_fcn_name)
        self.survival_fcn = met2
        self.survival_fcn_params = params["survival_fcn_params"]

        # local coordinate system
        # list of f0, s0, n0 functions for this material
        self.local_coordinate_system = coordinate_system

        #self.pre_stretch = params["pre_stretch"][0]
        self.G = params["G"][0]

        # Deformation gradient at time of material deposition
        self.F_cohort0 = dolfin.project(F_t,dolfin.TensorFunctionSpace(mesh,"DG",1)).copy()
        self.E_cohort0 = 0.5*(self.F_cohort0.T*self.F_cohort0 - dolfin.Identity(3))
        E_t = 0.5*(F_t.T*F_t - dolfin.Identity(3))

        # Initialize this cohort's strain energy function
        # Strain energy function for muscle fiber taken from https://doi.org/10.1016/j.actbio.2019.04.016
        self.sef = self.initialize_strain_energy_function(self.F_cohort0, self.E_cohort0, 0)
        
        self.constituent_phi = 1.0 #updated elsewhere for now

        self.phi_history = []
        self.cauchy_stress_history = []


#    def initialize_strain_energy_function(self, F_body, E_body, cohort_count):
    def initialize_strain_energy_function(self, F_body, E_body):
        
        """Initializes the strain energy function for this cohort. The strain 
        energy function depends on the elastic deformation, which is cohort 
        specific.

        :F_body: Body deformation gradient at time t
        :E_body: Green-Lagrange strain tensor calculated from F_body, doesn't 
                 need to be a separate argument
        :cohort_count: Used to determine whether this cohort is the first cohort
                       or not. The pre-stretch tensor needs to be the identity 
                       for initialization of the body.

        :return: W, a ufl product object representing the strain energy function
        """

        # F and E are given as for the entire body at some arbitrary time T
        F_cohort = F_body*dolfin.inv(self.F_cohort0)*self.G
        
        # Hard coding I
        I = dolfin.Identity(3)
        
        E_cohort = 0.5*(F_cohort.T*F_cohort - I)
        
        f0 = self.local_coordinate_system[0]
        s0 = self.local_coordinate_system[1]
        n0 = self.local_coordinate_system[2]
        
        Eff = dolfin.variable(dolfin.inner(f0, E_cohort*f0))
        Ess = dolfin.variable(dolfin.inner(s0, E_cohort*s0))
        Enn = dolfin.variable(dolfin.inner(n0, E_cohort*n0))
        Efs = dolfin.variable(dolfin.inner(f0, E_cohort*s0))
        Efn = dolfin.variable(dolfin.inner(f0, E_cohort*n0))
        Ens = dolfin.variable(dolfin.inner(n0, E_cohort*s0))
        Esf = dolfin.variable(dolfin.inner(s0, E_cohort*f0))
        Esn = dolfin.variable(dolfin.inner(s0, E_cohort*n0))
        Enf = dolfin.variable(dolfin.inner(n0, E_cohort*f0))

        f0 = self.local_coordinate_system[0]
        s0 = self.local_coordinate_system[1]
        n0 = self.local_coordinate_system[2]

        c1   = self.c1
        c2  = self.c2
        phi = self.phi

        alpha = dolfin.sqrt(2.0 * Eff + 1.0)

        W = c1*(dolfin.exp( c2* ufl.conditional(alpha > 1.0, alpha - 1.0, 0.0)**2.0) - 1.0)
        
        self.sef = W

        return W


    def calculate_local_pk2_tensor_field(self, E_cohort):
        
        """Calculate this cohort's Second Piola-Kirchhoff Stress tensor field, 
        either to record or use as stimulus.
    
        :E_cohort: This cohort's Green-Lagrange strain tensor
    
        :return: S_local, a ufl tensor, the PK2 stress tensor with respect to 
                 the local coordinate system (not global!)
        """

        # E coming in as E for this cohort
        f0 = self.local_coordinate_system[0]
        s0 = self.local_coordinate_system[1]
        n0 = self.local_coordinate_system[2]

        W = self.sef
        
        # Get local coordinate strain values
        Eff = dolfin.variable(dolfin.inner(f0, E_cohort*f0))
        Ess = dolfin.variable(dolfin.inner(s0, E_cohort*s0))
        Enn = dolfin.variable(dolfin.inner(n0, E_cohort*n0))
        Efs = dolfin.variable(dolfin.inner(f0, E_cohort*s0))
        Efn = dolfin.variable(dolfin.inner(f0, E_cohort*n0))
        Ens = dolfin.variable(dolfin.inner(n0, E_cohort*s0))
        Esf = dolfin.variable(dolfin.inner(s0, E_cohort*f0))
        Esn = dolfin.variable(dolfin.inner(s0, E_cohort*n0))
        Enf = dolfin.variable(dolfin.inner(n0, E_cohort*f0))
        
        alpha = dolfin.sqrt(2.0 * Eff + 1.0)
                
        # Dolfin differentiation is giving 0. This derivative is easy to do by hand
        Q = self.c2*ufl.conditional(alpha > 1.0, alpha - 1.0, 0.0)**2.0
        Sff = (2.0/alpha)* self.c1 * self.c2 * (ufl.conditional(alpha > 1.0, alpha, 1.0) - 1.0)*dolfin.exp(Q)
        S_local = Sff*dolfin.as_tensor(f0[i]*f0[j], (i,j))
                
        return S_local

    def calculate_local_cauchy_stress_field(self, F_body):
        
        """Calculate the local cauchy stress tensor field by transforming the PK2 stress.
    
        :F_body: Deformation gradient of body
    
        :return: cauchy, a ufl tensor that is the cauchy stress with respect to 
                 current coordinate system, pk2 as above, cur_local_coords, a 
                 list of vectors representing the current coordinate system for 
                 this cohort
        """
        # F input is body deformation gradient. Need to calculate cohort specific
        F_cohort = F_body*dolfin.inv(self.F_cohort0)*self.G
        I = dolfin.Identity(3) 
        E_cohort = 0.5*(F_cohort.T*F_cohort - I)
        J_cohort = dolfin.det(F_cohort)

        f = F_cohort*self.local_coordinate_system[0]
        s = F_cohort*self.local_coordinate_system[1]
        n = F_cohort*self.local_coordinate_system[2]
        
        # Normalize current coordinate system
        f = f/dolfin.sqrt(dolfin.inner(f,f))
        s = s/dolfin.sqrt(dolfin.inner(s,s))
        n = n/dolfin.sqrt(dolfin.inner(n,n))

        cur_local_coords = [f, s, n]

        pk2 = self.calculate_local_pk2_tensor_field(E_cohort)
        cauchy = (1.0/J_cohort)*F_cohort*pk2*F_cohort.T

        return cauchy, pk2, cur_local_coords

    def calculate_survival_proportion(self):
        
        """Returns the factor that represents the proportion of this cohort 
        that is remaining as calculated by this cohort's specified survival function.
   
        :return: survival_proportion, a dolfin function because deposition and 
                 mass removal can vary spatially
       """
       
        survival_proportion = self.survival_fcn(self.survival_fcn_params)
        return survival_proportion

class IsotropicMaterial():

    def __init__(self, params, coordinate_system, F_t):
        
        """Initializes a instance of this material class to become a cohort of a
        constituent. Sets the cohort's initial reference local coordinate 
        system, pre-stretch tensor G, survival function, and initializes this 
        cohort's strain energy function.

        :params:  dictionary of material specific parameters
        :coordinate_system: list of vectors forming the basis for this cohort's 
                            local reference coordinate system
        :F_t: Body deformation gradient at time of this cohort's creation. 
              Between this and the pre-stretch tensor G, the reference 
              configuration for this cohort can be solved for
        """
        
        # Material parameters
        self.c1   = params["c1"][0]
        self.phi = params["phi"][0]
        self.mesh = params["mesh"][0]
        mesh = self.mesh

        # Initial mass density function
        self.rho = dolfin.Function(dolfin.FunctionSpace(mesh,"DG",1))
        try:
            # if adding a new cohort of material based on stimulus
            temp = dolfin.project(params["rho"][0],dolfin.FunctionSpace(mesh,"DG",1))
            self.rho.assign(temp)
        except:
            # first cohort of this constituent, initialize to uniform  density
            self.rho.vector()[:] = params["rho"][0]

        # Each cohort of a constituent needs its own survival function
        survival_fcn_name = params["survival_fcn"][0]
        met2 = getattr(lifetime_functions,survival_fcn_name)
        self.survival_fcn = met2
        self.survival_fcn_params = params["survival_fcn_params"]

        # local coordinate system
        # list of f0, s0, n0 functions for this material
        self.local_coordinate_system = coordinate_system

        self.G = params["G"][0]

        # Deformation gradient at time of material deposition
        self.F_cohort0 = dolfin.project(F_t,dolfin.TensorFunctionSpace(mesh,"DG",1)).copy()
        self.E_cohort0 = 0.5*(self.F_cohort0.T*self.F_cohort0 - dolfin.Identity(3))
        E_t = 0.5*(F_t.T*F_t - dolfin.Identity(3))

        # Initialize this cohort's strain energy function
        # Isotropic hyperelastic Neo-Hookean material https://doi.org/10.1016/j.actbio.2019.04.016
        self.sef = self.initialize_strain_energy_function(self.F_cohort0, self.E_cohort0, 0)
        
        self.constituent_phi = 1.0 #updated elsewhere for now

        self.phi_history = []
        self.cauchy_stress_history = []


    def initialize_strain_energy_function(self, F_body, E_body, cohort_count):
        
        """Initializes the strain energy function for this cohort. The strain 
        energy function depends on the elastic deformation, which is cohort 
        specific.

        :F_body: Body deformation gradient at time t
        :E_body: Green-Lagrange strain tensor calculated from F_body, doesn't 
                 need to be a separate argument
        :cohort_count: Used to determine whether this cohort is the first cohort
                       or not. The pre-stretch tensor needs to be the identity 
                       for initialization of the body.

        :return: W, a ufl product object representing the strain energy function
        """

        # F and E are given as for the entire body at some arbitrary time T
        F_cohort = F_body*dolfin.inv(self.F_cohort0)*self.G
        C_cohort = F_body.T*F_body
        I1 = dolfin.tr(C_cohort)
        c1   = self.c1
        phi = self.phi
        
        W = (c1/2.0)*(I1 - 3.0)
        
        self.sef = W

        return W


    def calculate_local_pk2_tensor_field(self, E_cohort):
        
        """Calculate this cohort's Second Piola-Kirchhoff Stress tensor field, 
        either to record or use as stimulus.
    
        :E_cohort: This cohort's Green-Lagrange strain tensor
    
        :return: S_local, a ufl tensor, the PK2 stress tensor with respect to 
                 the local coordinate system (not global!)
        """
        
        C = dolfin.variable(2.0*E_cohort + dolfin.Identity(3))
        I1 = dolfin.variable(dolfin.tr(C))
        c1 = self.c1
        W = (c1/2.0)*(I1 - 3.0)
        
        S_local = 2.0*dolfin.diff(W,C)

        return S_local

    def calculate_local_cauchy_stress_field(self, F_body):
        
        """Calculate the local cauchy stress tensor field by transforming the PK2 stress.
    
        :F_body: Deformation gradient of body
    
        :return: cauchy, a ufl tensor that is the cauchy stress with respect to 
                 current coordinate system, pk2 as above, cur_local_coords, a 
                 list of vectors representing the current coordinate system for 
                 this cohort
        """
        
        # F input is body deformation gradient. Need to calculate cohort specific
        F_cohort = F_body*dolfin.inv(self.F_cohort0)*self.G
        I = dolfin.Identity(3) # will this need to be identity in local coordinates?
        E_cohort = 0.5*(F_cohort.T*F_cohort - I)
        J_cohort = dolfin.det(F_cohort)

        f = F_cohort*self.local_coordinate_system[0]
        s = F_cohort*self.local_coordinate_system[1]
        n = F_cohort*self.local_coordinate_system[2]
        
        # Normalize current coordinate system
        f = f/dolfin.sqrt(dolfin.inner(f,f))
        s = s/dolfin.sqrt(dolfin.inner(s,s))
        n = n/dolfin.sqrt(dolfin.inner(n,n))

        cur_local_coords = [f, s, n]

        pk2 = self.calculate_local_pk2_tensor_field(E_cohort)
        cauchy = (1.0/J_cohort)*F_cohort*pk2*F_cohort.T

        return cauchy, pk2, cur_local_coords

    def calculate_survival_proportion(self):
        
        """Returns the factor that represents the proportion of this cohort 
        that is remaining as calculated by this cohort's specified survival function.
    
        :return: survival_proportion, a dolfin function because deposition and 
                 mass removal can vary spatially
        """
        
        survival_proportion = self.survival_fcn(self.survival_fcn_params)
        
        return survival_proportion
