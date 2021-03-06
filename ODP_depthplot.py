#!/usr/bin/env python
import pmag,sys,exceptions,matplotlib
matplotlib.use("TkAgg")
import pylab
pylab.ion()
def main():
    """
    NAME 
        ODP_depthplot.py

    DESCRIPTION
        plots various measurements versus core_depth

    SYNTAX
        ODP_depthplot.py [command line optins]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input magic_measurments format file from magic
        -fsum FILE: specify input ODP core summary csv file
        -fwig FILE: specify input depth,wiggle to plot, in magic format with sample_core_depth key for depth
        -fsa FILE: specify input er_samples format file from magic
        -fsp FILE sym size: specify input zeq_specimen format file from magic, sym and size
        -LP [AF,T,ARM,IRM, X] step [in mT,C,mT,mT, mass/vol] to plot 
        -sym SYM SIZE, symbol, size for data points (e.g., ro 5, bs 10, g^ 10 for red dot, blue square, green triangle), default is blue dot at 5 pt
        -D do not plot declination
        -M do not plot magnetization
        -log  plot magnetization  on a log scale
        -L do not connect dots with a line
        -I do not plot inclination
        -S do not plot subsample blanket treatment data
        -d min max [in m] depth range to plot
        -n normalize by weight in er_specimen table
        -Iex: plot the expected inc at lat - only available for results with lat info in file
        -ts TS amin amax: plot the GPTS for the time interval between amin and amax (numbers in Ma)
           TS: [ck95, gts04] 

     DEFAULTS:
         Measurements file: magic_measurements.txt
         Samples file: er_samples.txt
         NRM step
         Summary file: none
    """
    meas_file='magic_measurements.txt'
    samp_file='er_samples.txt'
    wt_file=''
    width=10
    sym,size='bo',5
    Ssym,Ssize='ws',5
    method,fmt="LT-NO",'.pdf'
    step=0
    pcol=3
    pel=3
    pltD,pltI,pltM,pltL,pltS=1,1,1,1,1
    logit=0
    maxInt=-1000
    minInt=1e10
    maxSuc=-1000
    minSuc=10000
    plotexp,pTS=0,0
    dir_path="."
    sum_file=""
    suc_file=""
    spc_file=""
    ngr_file=""
    wig_file=""
    title=""
    if '-WD' in sys.argv: 
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    norm=0
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-L' in sys.argv:
        pltL=0
    if '-S' in sys.argv:
        pltS=0
    if '-D' in sys.argv:
        pltD=0
        pcol-=1
        pel-=1
        width-=2
    if '-I' in sys.argv:
        pltI=0
        pcol-=1
        pel-=1
        width-=2
    if '-M' in sys.argv:
        pltM=0
        pcol-=1
        pel-=1
        width-=2
    if '-log' in sys.argv:logit=1
    if '-sym' in sys.argv:
        ind=sys.argv.index('-sym')
        sym=sys.argv[ind+1]
        size=float(sys.argv[ind+2])
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        meas_file=sys.argv[ind+1]
    if '-fsa' in sys.argv:
        ind=sys.argv.index('-fsa')
        samp_file=sys.argv[ind+1]
    if '-fsp' in sys.argv:
        ind=sys.argv.index('-fsp')
        spc_file=dir_path+'/'+sys.argv[ind+1]
        spc_sym=sys.argv[ind+2]
        spc_size=float(sys.argv[ind+3])
    if '-fwig' in sys.argv:
        ind=sys.argv.index('-fwig')
        wig_file=dir_path+'/'+sys.argv[ind+1]
        pcol+=1
        width+=2
    if '-fsum' in sys.argv:
        ind=sys.argv.index('-fsum')
        sum_file=sys.argv[ind+1]
        sum_file=dir_path+'/'+sys.argv[ind+1]
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt='.'+sys.argv[ind+1]
    if '-LP' in sys.argv:
        ind=sys.argv.index('-LP')
        meth=sys.argv[ind+1]
        if meth=="AF":
            step=float(sys.argv[ind+2])*1e-3
            method='LT-AF-Z'
        elif meth== 'T':
            step=float(sys.argv[ind+2])+273
            method='LT-T-Z'
        elif meth== 'ARM':
            method='LT-AF-I'
            step=float(sys.argv[ind+2])*1e-3
        elif meth== 'IRM':
            method='LT-IRM'
            step=float(sys.argv[ind+2])*1e-3
        elif meth== 'X':
            method='LP-X'
            pcol+=1
            if sys.argv[ind+2]=='mass':
                suc_key='measurement_chi_mass'
            elif sys.argv[ind+2]=='vol':
                suc_key='measurement_chi_volume'
            else:
                print 'error in susceptibility units'
                sys.exit()
        else:
           print 'method not supported'
           sys.exit()
    if '-n' in sys.argv: 
        ind=sys.argv.index('-n')
        wt_file=dir_path+'/'+sys.argv[ind+1]
        norm=1
    dmin,dmax=-1,-1
    if '-d' in sys.argv:
        ind=sys.argv.index('-d')
        dmin=float(sys.argv[ind+1])
        dmax=float(sys.argv[ind+2])
    if '-ts' in sys.argv:
        ind=sys.argv.index('-ts')
        ts=sys.argv[ind+1]
        amin=float(sys.argv[ind+2])
        amax=float(sys.argv[ind+3])
        pTS=1
        pcol+=1
        width+=2
    #
    #
    # get data read in
    meas_file=dir_path+'/'+meas_file
    samp_file=dir_path+'/'+samp_file
    Meas,file_type=pmag.magic_read(meas_file) 
    print len(Meas), ' measurements read in from ',meas_file
    Samps,file_type=pmag.magic_read(samp_file) 
    if spc_file!="":Specs,file_type=pmag.magic_read(spc_file) 
    if norm==1:
        ErSpecs,file_type=pmag.magic_read(wt_file) 
        print len(ErSpecs), ' specimens read in from ',wt_file
    Cores=[] 
    if sum_file!="":
        input=open(sum_file,'rU').readlines()
        keys=input[1].replace('\n','').split(',') # splits on underscores
        for line in input[2:]:
            if 'TOTALS' not in line:
                CoreRec={}
                for k in range(len(keys)):CoreRec[keys[k]]=line.split(',')[k]
                Cores.append(CoreRec)
        if len(Cores)==0:
            print 'no Core depth information available: import core summary file'
            sum_file=""
    Data=[]
    for rec in Meas:
        for samp in Samps:
            if samp['er_sample_name']== rec['er_sample_name'] and 'sample_core_depth' in samp.keys() and samp['sample_core_depth']!="":
                rec['core_depth'] = float(samp['sample_core_depth'])
                rec['magic_method_codes'] = rec['magic_method_codes']+':'+samp['magic_method_codes']
                if norm==1:
                    for spec in ErSpecs:
                        if spec['er_sample_name']== rec['er_sample_name'] and 'specimen_weight' in spec.keys() and spec['specimen_weight']!="":
                            rec['specimen_weight'] = spec['specimen_weight']
                            Data.append(rec) # fish out data with core_depth and (if needed) weights
                else:
                    Data.append(rec) # fish out data with core_depth and (if needed) weights
                if title=="":
                   pieces=samp['er_sample_name'].split('-')
                   title=pieces[0]+'-'+pieces[1]
    SData=pmag.sort_diclist(Data,'core_depth')
    xlab="Depth (mbsf)"
    # collect the data for plotting declination
    Depths,Decs,Incs,Ints=[],[],[],[]
    SDepths,SDecs,SIncs,SInts=[],[],[],[]
    SSucs=[]
    samples=[]
    methods,steps=[],[]
    for rec in SData:
        if "magic_method_codes" in rec.keys():
            meths=rec["magic_method_codes"].split(":")
            if method in meths:
                if step==0 or ('LT-AF-Z' in method and float(rec['treatment_ac_field'])==step) or ('LT-T-Z' in method and float(rec['treatment_temp'])==step) or ('LT-AF-I' in method and float(rec['treatment_ac_field'])==step) or ('LT-IRM' in method and float(rec['treatment_dc_field'])==step) or ('LP-X' in method and rec[suc_key] in rec.keys() and rec[suc_key]!=""):
                    if dmax==-1 or float(rec['core_depth'])<dmax and float(rec['core_depth'])>dmin:
                        if  'FS-SS-C' not in meths: # make sure it is desired lab treatment step 
                            Depths.append((rec['core_depth']))
                            if pltD==1:Decs.append(float(rec['measurement_dec']))
                            if pltI==1:Incs.append(float(rec['measurement_inc']))
                            if norm==0 and pltM==1:Ints.append(float(rec['measurement_magn_moment']))
                            if norm==1 and pltM==1:Ints.append(float(rec['measurement_magn_moment'])/float(rec['specimen_weight']))
                            if len(Ints)>1 and Ints[-1]>maxInt:maxInt=Ints[-1]
                            if len(Ints)>1 and Ints[-1]<minInt:minInt=Ints[-1]
                        elif  pltS==1: # make sure it is desired lab treatment step 
                            SDepths.append((rec['core_depth']))
                            if pltD==1:SDecs.append(float(rec['measurement_dec']))
                            if pltI==1:SIncs.append(float(rec['measurement_inc']))
                            if norm==0 and pltM==1:SInts.append(float(rec['measurement_magn_moment']))
                            if norm==1 and pltM==1:SInts.append(float(rec['measurement_magn_moment'])/float(rec['specimen_weight']))
                            if len(SInts)>1 and SInts[-1]>maxInt:maxInt=SInts[-1]
                            if len(SInts)>1 and SInts[-1]<minInt:minInt=SInts[-1]
                            if method=="LP-X": 
                                SSucs.append(float(rec[suc_key]))
                                if SSucs[-1]>maxSuc:maxSuc=SSucs[-1]
                                if SSucs[-1]<minSuc:minSuc=SSucs[-1]
                    elif len(Depths) and len(SDepths)==0:
                        for meth in meths:
                            if 'LT-AF-Z' in meth:
                                thisstep='%7.1f'%(float(rec['treatment_ac_field'])*1e3)
                                if thisstep not in steps:steps.append(thisstep)
                                if 'AF' not in methods:methods.append('AF')
                            if 'LT-T-Z' in meth:
                                thisstep='%7.1f'%(float(rec['treatment_ac_field'])-273.)
                                if thisstep not in steps:steps.append(thisstep)
                                if 'T' not in methods:methods.append('T')
                            if 'LT-T-I' in meth:
                                thisstep='%7.1f'%(float(rec['treatment_ac_field'])*1e3)
                                if thisstep not in steps:steps.append(thisstep)
                                if 'ARM' not in methods:methods.append('ARM')
                            if 'LT-IRM' in meth:
                                thisstep='%7.1f'%(float(rec['treatment_dc_field'])*1e3)
                                if thisstep not in steps:steps.append(thisstep)
                                if 'IRM' not in methods:methods.append('IRM')
    if len(Depths)==0 and len(SDepths)==0:
        print 'no data matched your request, try a different lab treatment '
        print 'available treatment types: ',methods
        print 'available treatment steps: ',steps
#        sys.exit()
    if dmin==-1:
        if len(Depths)>0: dmin,dmax=Depths[0],Depths[-1]
        if pltS==1 and len(SDepths)>0:
            if SDepths[0]<dmin:dmin=SDepths[0]
            if SDepths[-1]>dmax:dmax=SDepths[-1]
    SpecDepths,SpecDecs,SpecIncs=[],[],[]
    if spc_file!="" and pltS==1: # add depths to spec data
        for spec in Specs:
            for samp in Samps:
                if samp['er_sample_name']== spec['er_sample_name'] and 'sample_core_depth' in samp.keys() and samp['sample_core_depth']!="":
                    meths=samp['magic_method_codes'].split(":")
                    if 'DE-BFP' not in meths:
                        SpecDepths.append(float(samp['sample_core_depth'])) # fish out data with core_depth
                        SpecDecs.append(float(spec['specimen_dec'])) # fish out data with core_depth
                        SpecIncs.append(float(spec['specimen_inc'])) # fish out data with core_depth
    Susc,Sus_depths=[],[]
    if suc_file!="":
        sucdat=open(suc_file,'rU').readlines()
        keys=sucdat[0].replace('\n','').split(',') # splits on underscores
        for line in sucdat[1:]:
            SucRec={}
            for k in range(len(keys)):SucRec[keys[k]]=line.split(',')[k]
            if float(SucRec['Top Depth (m)'])<dmax and float(SucRec['Top Depth (m)'])>dmin and SucRec['Magnetic Susceptibility (80 mm)']!="":
                Susc.append(float(SucRec['Magnetic Susceptibility (80 mm)']))
                if Susc[-1]>maxSuc:maxSuc=Susc[-1]
                if Susc[-1]<minSuc:minSuc=Susc[-1]
                Sus_depths.append(float(SucRec['Top Depth (m)']))
    WIG,WIG_depths=[],[]
    if wig_file!="":
        wigdat,file_type=pmag.magic_read(wig_file)
        swigdat=pmag.sort_diclist(wigdat,'sample_core_depth')
        keys=wigdat[0].keys()
        for key in keys:
            if key!="sample_core_depth":
                plt_key=key
                break
        for wig in swigdat:
            if float(wig['sample_core_depth'])<dmax and float(wig['sample_core_depth'])>dmin:
                WIG.append(float(wig[plt_key]))
                WIG_depths.append(float(wig['sample_core_depth']))
    tint=4.5
    plt=1
    if len(Decs)>0 and len(Depths)>0 or (len(SpecDecs)>0 and len(SpecDepths)>0) or (len(SDecs)>0 and len(SDepths)>0) or (len(SInts)>0 and len(SDepths)>0) or (len(SIncs)>0 and len(SDepths)>0):
        for pow in range(-10,10):
            if maxInt*10**pow>1:break
        if logit==0:
            for k in range(len(Ints)):
                Ints[k]=Ints[k]*10**pow
            for k in range(len(SInts)):
                SInts[k]=SInts[k]*10**pow
        pylab.figure(1,figsize=(width,8))
        version_num=pmag.get_version()
        pylab.figtext(.02,.01,version_num)
        if pltD==1:
            pylab.subplot(1,pcol,plt)
            if pltL==1:pylab.plot(Decs,Depths,'k') 
            if len(Decs)>0:pylab.plot(Decs,Depths,sym,markersize=size) 
            if len(Decs)==0 and pltL==1 and len(SDecs)>0:pylab.plot(SDecs,SDepths,'k')
            if len(SDecs)>0:pylab.plot(SDecs,SDepths,Ssym,markersize=Ssize) 
            if spc_file!="":pylab.plot(SpecDecs,SpecDepths,spc_sym,markersize=spc_size) 
            if sum_file!="":
                for core in Cores:
                     depth=float(core['Core Top (m)']) 
                     if depth>dmin and depth<dmax:
                        pylab.plot([0,360.],[depth,depth],'b--')
                        if pel==plt:pylab.text(360,depth+tint,core['Core #']+core['Core Type'])
            if pel==plt:
                pylab.axis([0,400,dmax,dmin])
            else:
                pylab.axis([0,360.,dmax,dmin])
            pylab.xlabel('Declination')
            pylab.ylabel('Depth (mbsf)')
            if title!="":pylab.title(title)
            title=""
            plt+=1 
    if pltI==1:
            pylab.subplot(1,pcol,plt)
            if pltL==1:pylab.plot(Incs,Depths,'k') 
            if len(Incs)>0:pylab.plot(Incs,Depths,sym,markersize=size) 
            if len(Incs)==0 and pltL==1 and len(SIncs)>0:pylab.plot(SIncs,SDepths,'k')
            if len(SIncs)>0:pylab.plot(SIncs,SDepths,Ssym,markersize=Ssize) 
            if spc_file!="":pylab.plot(SpecIncs,SpecDepths,spc_sym,markersize=spc_size) 
            if sum_file!="":
                for core in Cores:
                     depth=float(core['Core Top (m)']) 
                     if depth>dmin and depth<dmax:
                         if pel==plt:pylab.text(90,depth+tint,core['Core #']+core['Core Type'])
                         pylab.plot([-90,90],[depth,depth],'b--')
            pylab.plot([0,0],[dmax,dmin],'k-') 
            if pel==plt:
                pylab.axis([-90,110,dmax,dmin])
            else:
                pylab.axis([-90,90,dmax,dmin])
            pylab.xlabel('Inclination')
            pylab.ylabel('')
            if title!="":pylab.title(title)
            title=""
            plt+=1
    if pltM==1 and len(Ints)>0 or len(SInts)>0:
            pylab.subplot(1,pcol,plt)
            if logit==0:
                if pltL==1 and len(Ints)>0: pylab.plot(Ints,Depths,'k') 
                if len(Ints)>0:pylab.plot(Ints,Depths,sym,markersize=size) 
                if len(Ints)==0 and pltL==1 and len(SInts)>0:pylab.plot(SInts,SDepths,'k-')
                if len(SInts)>0:pylab.plot(SInts,SDepths,Ssym,markersize=Ssize) 
                if sum_file!="":
                    for core in Cores:
                         depth=float(core['Core Top (m)']) 
                         pylab.plot([0,maxInt*10**pow+.1],[depth,depth],'b--')
                         if depth>dmin and depth<dmax:pylab.text(maxInt*10**pow-.2*maxInt*10**pow,depth+tint,core['Core #']+core['Core Type'])
                pylab.axis([0,maxInt*10**pow+.1,dmax,dmin])
                if norm==0:
                    pylab.xlabel('%s %i %s'%('Intensity (10^-',pow,' Am^2)'))
                else:
                    pylab.xlabel('%s %i %s'%('Intensity (10^-',pow,' Am^2/kg)'))
            else:
                if pltL==1: pylab.semilogx(Ints,Depths,'k') 
                if len(Ints)>0:pylab.semilogx(Ints,Depths,sym,markersize=size) 
                if len(Ints)==0 and pltL==1 and len(SInts)>0:pylab.semilogx(SInts,SDepths,'k')
                if len(Ints)==0 and pltL==1 and len(SInts)>0:pylab.semilogx(SInts,SDepths,'k')
                if len(SInts)>0:pylab.semilogx(SInts,SDepths,Ssym,markersize=Ssize) 
                if sum_file!="":
                    for core in Cores:
                         depth=float(core['Core Top (m)']) 
                         pylab.semilogx([minInt,maxInt],[depth,depth],'b--')
                         if depth>dmin and depth<dmax:pylab.text(maxInt-.2*maxInt,depth+tint,core['Core #']+core['Core Type'])
                pylab.axis([0,maxInt,dmax,dmin])
                if norm==0:
                    pylab.xlabel('Intensity (Am^2)')
                else:
                    pylab.xlabel('Intensity (Am^2/kg)')
            if title!="":pylab.title(title)
            title=""
            plt+=1
    if suc_file!="" or len(SSucs)>0:
            pylab.subplot(1,pcol,plt)
            if len(Susc)>0:
                if pltL==1:pylab.plot(Susc,Sus_depths,'k') 
                if logit==0:pylab.plot(Susc,Sus_depths,sym,markersize=size) 
                if logit==1:pylab.semilogx(Susc,Sus_depths,sym,markersize=size) 
            if len(SSucs)>0:
                if logit==0:pylab.plot(SSucs,SDepths,sym,markersize=size) 
                if logit==1:pylab.semilogx(SSucs,SDepths,sym,markersize=size) 
            if sum_file!="":
                for core in Cores:
                     depth=float(core['Core Top (m)']) 
                     if logit==0:pylab.plot([minSuc,maxSuc],[depth,depth],'b--')
                     if logit==1:pylab.semilogx([minSuc,maxSuc],[depth,depth],'b--')
            pylab.axis([minSuc,maxSuc,dmax,dmin])
            pylab.xlabel('Susceptibility')
            if title!="":pylab.title(title)
            title=""
            plt+=1
    if wig_file!="":
            pylab.subplot(1,pcol,plt)
            pylab.plot(WIG,WIG_depths,'k') 
            if sum_file!="":
                for core in Cores:
                     depth=float(core['Core Top (m)']) 
                     pylab.plot([WIG[0],WIG[-1]],[depth,depth],'b--')
            pylab.axis([min(WIG),max(WIG),dmax,dmin])
            pylab.xlabel(plt_key)
            if title!="":pylab.title(title)
            title=""
            plt+=1
    if pTS==1:
            ax1=pylab.subplot(1,pcol,plt)
            plt+=1
            TS,Chrons=pmag.get_TS(ts)
            p=1
            X,Y=[],[]
            for d in TS:
                if d<=amax and d>=amin:
                    if len(X)==0:
                        ind=TS.index(d)
                        X.append(TS[ind-1])
                        Y.append(p%2)
                    X.append(d)
                    Y.append(p%2)
                    p+=1
                    X.append(d)
                    Y.append(p%2)
                else: 
                    X.append(amax)
                    Y.append(p%2)
                #    isign=-1
            ax1.plot(Y,X,'k')
            ax1.plot([0,1,1,0,0],[amin,amin,amax,amax,amin],'k-')
            ax1.axis([-.25,1.5,amax,amin])
            ax2=ax1.twinx()
            pylab.ylabel("Age (Ma): "+ts) 
            for c in Chrons:
                #     isign=-1*isign 
                #     if isign>0: off=1.05
                     if c[1]>=amin and c[1]<amax:
                         ax2.text(1.05,c[1],c[0])
            ax2.axis([-.25,1.5,amax,amin])
    pylab.draw()
    ans=raw_input("Press return to quit  ")
    sys.exit()
main()
