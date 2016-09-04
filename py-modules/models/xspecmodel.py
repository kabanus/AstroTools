try:
    import xspec
    xspec.XspecSettings.chatter.fset(0,0)

    from collections import OrderedDict
    from model import _singleModel,modelExport
    from numpy import array_equal,array
    
    @modelExport
    class Xspec(_singleModel):
        description = "Any Xspec model(Same syntax)"
        def __init__(self, modelString):
            _singleModel.__init__(self)
            self.model    = xspec.Model(modelString)
            self.plot     = xspec.plot.Plot
            self.params   = OrderedDict(((str(i)+':'+self.model(i).name,self.model(i).values[0]) 
                                    for i in range(1,self.model.nParameters+1)))
            self.energies = ()
            self.efile    = 'fitterModel.Energies'
            self.plot('model')
            self.plot.xAxis='keV'

        def update(self):
            self.plot()
            self.ehash = array(self.plot.model())

        def reload(self,atrange):
            self.energies = atrange
            fd = open(self.efile,'w')
            #We calculate at actual bin (we calculated middle before)
            lastenergy = 1.5*self.energies[0]-0.5*self.energies[1]
            for i in range(len(self.energies)):
                fd.write(str(lastenergy)+'\n')
                lastenergy = 2*self.energies[i]-lastenergy
            fd.write(str(lastenergy)+'\n')
            fd.close()
            xspec.AllModels.setEnergies(self.efile)
            self.update()
    
        def _calculate(self, atrange):
            if not array_equal(atrange,self.energies):
                self.reload(atrange)
            elif self.changed:
                self.update()
            return self.ehash

        def setp(self, pDict):
            _singleModel.setp(self,pDict)
            self.model.setPars(*self.params.values())

except ImportError:
    print "Warning: No XSPEC module found, won't be able to use XSPEC models. If this is unexpected, make sure you're in an HEADAS environemnt."

