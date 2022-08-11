# @Author: charlesmann
# @Date:   2022-03-17T09:57:47+01:00
# @Last modified by:   charlesmann
# @Last modified time: 2022-03-25T13:52:31+01:00

import dolfin
import materials
import lifetime_functions

class Constituent():

    def __init__(
        self,
        init_cohort_params,
        local_coordinate_system,
        F
        ):
        """Initialize constituent class with one cohort for t = 0"""
        # Initialize the add_cohort function using the specific material for this constituent
        material_type = init_cohort_params["material_type"][0]
        met = getattr(materials,material_type)
        self.add_material = met

        self.mesh = init_cohort_params["mesh"][0]

        self.cohorts = []

        self.i=0

        self.cohort_template = init_cohort_params
        self.local_coordinate_system = local_coordinate_system # needs to be general, as this may change with time

        mass_fcn_name = init_cohort_params["mass_production_fcn"][0]
        met = getattr(lifetime_functions,mass_fcn_name)
        self.mass_production_fcn = met
        self.mass_production_fcn_params = init_cohort_params["mass_production_fcn_params"]

        self.user_specified_pre_stretch = init_cohort_params["pre_stretch_for_F0"][0]

        # Initialize the first cohort, can't be an "empty" material
        self.cohort_template = init_cohort_params
        cohort_0 = self.add_cohort(F, 1, 0)
        self.cohorts.append(cohort_0)

        # constituent's initial mass is that of the initial cohort
        self.mass = cohort_0.m

        # constituent's strain energy function is that of the initial cohort
        #self.sef += cohort_0.calculate_sef()

        # Create a "template" of parameters for new cohorts added
        # This template can be modified based on some law if changes
        # in material properties (or coordinate system) are desired

        # Does this need to be a certain type of copy so existing cohort params
        # aren't altered?
        # temporarily specifying reference for cohorts
        #init_cohort_params["pre_stretch_for_F0"][0] = dolfin.Constant(1.00) # so all new material have a new reference config
        self.cohort_template = init_cohort_params

        self.cohort_threshold = init_cohort_params["removal_mass_threshold"][0]

        self.sef = 0.0

        self.dx = init_cohort_params["dx"][0] # needed for mass calculation

    def add_cohort(self, F, first, problem):
        # Shortcut for first cohort, need a general fix
        """Add a cohort of material according to the material's mass production"""
        # calculate mass addition field based on stimulus
        # Growth needs to be done at the constituent level?
        # Calculate a new mass field, and use that to initialize a cohort?
        new_mass_field = dolfin.Function(dolfin.FunctionSpace(self.mesh,"DG",1))
        cauchy_stress_constituent = dolfin.Function(dolfin.FunctionSpace(self.mesh,"DG",1))
        cauchy_stress_constituent.vector()[:] = 0.0
        # Need to generalize this, may not always use cauchy stress as stimulus
        for material_cohorts in self.cohorts:
            cauchy_cohort, lcs = material_cohorts.calculate_local_cauchy_stress_field(F)
            #print(cauchy_cohort.vector().get_local())
            cauchy_stress_constituent += dolfin.inner(lcs[0],cauchy_cohort*lcs[0])

        #cauchy_stress_file = dolfin.File('cauchy_stress.pvd')
        #c = dolfin.project(cauchy_stress_constituent,dolfin.FunctionSpace(self.mesh,"DG",1))
        #cauchy_stress_file << c

        # Need to standardize input and outpt to mass production functions
        #new_mass_field, x = self.mass_production_fcn(cauchy_stress_constituent)
        #new_mass_field = self.mass_production_fcn(self.mass_production_fcn_params, self.mesh)
        #mass_field_proj = dolfin.project(new_mass_field,dolfin.FunctionSpace(self.mesh,"DG",1))
        #mass_field_file = dolfin.File('output/new_mass_field'+str(self.i)+'.pvd')
        #cauchy_stress_file = dolfin.File('output/cauchy'+str(self.i)+'.pvd')
        #cauchy_stress_file << dolfin.project(cauchy_stress_constituent,dolfin.FunctionSpace(self.mesh,"DG",1))
        self.i+=1
        #mass_field_file << mass_field_proj
        #deviation_file = dolfin.File('output/deviation.pvd')
        #dev = dolfin.project(x, dolfin.FunctionSpace(self.mesh,"DG",1))
        #deviation_file << dev
        if first:
            self.cohort_template["m"] = self.cohort_template["m0"]
            self.cohort_template["pre_stretch_for_F0"] = [1.0]
        else:
            self.cohort_template["pre_stretch_for_F0"] = [self.user_specified_pre_stretch]
            new_mass_field = self.mass_production_fcn(problem.mass_production_stimulus, self.mesh)
            self.cohort_template["m"] =[new_mass_field]
        cohort = self.add_material(self.cohort_template, self.local_coordinate_system, F)
        return cohort

    def get_mass(self):
        """Calculate and return the mass for this constituent"""
        self.calculate_mass()
        return self.mass

    def calculate_mass(self):
        """Sums the mass of each cohort of material to give constituent's mass"""
        mass = 0.0
        for cohort in self.cohorts:
            mass += cohort.m
        self.mass = mass
        return

    def remove_cohorts(self):
        """Removes cohort of material if mass falls below a threshold"""
        # Each cohort should have its own mass production and survival functions
        tol = 1E-6
        for cohort in self.cohorts:
            cohort.m *= cohort.calculate_survival_proportion()
            #print(dolfin.assemble(cohort.m*self.dx))
            #print(self.cohort_threshold)
        self.cohorts = [item for item in self.cohorts if dolfin.assemble(item.m*self.dx) >= (self.cohort_threshold-tol)]
        return

    def assign_cohort_phis(self, body_mass):
        """Updates each cohort's volume fraction"""
        for cohort in self.cohorts:
            cohort.phi = cohort.m/body_mass
            cohort.phi_history.append(dolfin.project(cohort.phi,dolfin.FunctionSpace(self.mesh,"DG",1)).vector().get_local()[0]) # checking something in case of homogeneous deformation
        return

    def sum_cohort_sefs(self,F):
        """Add the weighted strain energy functions from each cohort.
           Each cohort potentially has its own reference configuration,
           so its deformation gradient is unique"""
        sef = 0.0
        for cohort in self.cohorts:
            #sef += cohort.sef
            E = 0.5*(F.T*F - dolfin.Identity(3))
            sef += cohort.initialize_strain_energy_function(F,E)
        return sef
