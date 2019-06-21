import os, sys, optparse

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def submit():

    print bcolors.HEADER
    print '#######################################################################'
    print '                  Starting job(s) submission...                        '
    print '#######################################################################' + bcolors.ENDC

    parser = optparse.OptionParser(usage='usage: %prog [opts] FilenameWithSamples', version='%prog 1.0')
    parser.add_option('-q', '--queue', action='store', type=str, dest='queue', default='tomorrow', help='Name of the queue to be used')
    parser.add_option('-d', '--directory', action='store', type=str, dest='inputDir', default='', help='Name of the directory where the samples can be found')
    parser.add_option('-o', '--output', action='store', type=str, dest='outputDir', default=os.getcwd()+'/jobs/', help='Output directory')
    parser.add_option('-w', '--work', action='store', type=str, dest='workDir', default=os.getcwd(), help='Working directory')
    parser.add_option('-y', '--year', action='store', type=str, dest='year', default="", help='Year of the dataset considered (2016, 2017 or 2018)')
    parser.add_option('-t', '--test', action='store_true', dest='doNotSend', default=False, help='Do not send the jobs to the queue, to be used for testing')
    (opts, args) = parser.parse_args()

    # Read the options given
    queue        = opts.queue
    inputDir     = opts.inputDir
    outputDir    = opts.outputDir
    workDir      = opts.workDir
    year         = opts.year
    doNotSend    = opts.doNotSend

    if not os.path.exists("jobs"):
        os.makedirs("jobs")

    if not os.path.exists("results"):
        os.makedirs("results")

    #Check the options given
    if queue not in ['espresso', 'microcentury', 'longlunch', 'workday', 'tomorrow', 'testmatch', 'nextweek']:
        print "Queue not found.... Using tomorrow as default value."
        queue = "tomorrow"
    
    if year == "":
        print "BE CAREFUL! You did not introduce any year, so you considering that you are reading 2016 files by default"
        year = "2016"
    elif year != "2016" and year != "2017" and year != "2018":
        print "The year given does not seem to be valid"
        return

    if not inputDir:
        print "You have to specify the directory read the input files can be found using the -d option."
        return

    #Print the options chosen to the user
    print bcolors.OKBLUE
    print '#######################################################################'
    print '                  Summary of options chosen                        '
    print '#######################################################################'

    print "Queue: "+queue;
    print "Year: "+year;
    print "Input directory: "+inputDir
    print "Output directory: "+outputDir

    print '#######################################################################' + bcolors.ENDC

    #Read the files from the input directory
    jobs = []
    samples = os.listdir(inputDir)
    
    for sample in samples:

        if year == "2016":
            if("DYJetsToLL_M-50_ext2__" in sample)or ("DYJetsToLL_M-10to50-LO_" in sample) or ("WJetsToLNu__" in sample) or ("DoubleMuon" in sample) or ("DoubleEG" in sample): 
                jobs.append(sample)

        elif year == "2017":
            if ("DYJetsToLL_M-10to50-LO_" in sample) or ("DYJetsToLL_M-50__" in sample) or ("WJetsToLNu-LO__" in sample) or ("DoubleMuon" in sample) or ("SingleElectron" in sample):
            #if "GJets" in sample:
                jobs.append(sample)

        elif year == "2018":
            if ("DYJetsToLL_M-10to50-LO_" in sample) or ("DYJetsToLL_M-50-LO__" in sample) or ("WJetsToLNu-LO__" in sample) or ("DoubleMuon" in sample) or ("DoubleEG" in sample):
                jobs.append(sample)

    if len(jobs) == 0:
        print "No file matching the requirements in the directory given has been found"
        return

    jobsList = []

    for job in jobs:
        
        if job == "" or job == "\n" or ("part" not in job):
            continue

        #Check the format of the sample names and correct it if necessary
        if "nanoLatino_" not in job:
            job = "nanoLatino_"+job
            
        if ".root" in sample:
            job = job[:-5]

        #Remove strange characters from job name
        job = job.strip(' \t\n\r')

        jobFileName = outputDir+job + ".sh"
        subFileName = outputDir+job + ".sub"
        errFileName = outputDir+job + ".err"
        outFileName = outputDir+job + ".out"
        logFileName = outputDir+job + ".log"
        jidFileName = outputDir+job + ".jid"
        
        jobFile = open(jobFileName, "w+")
        jobFile.write("#!/bin/sh \n")
        jobFile.write("cd - \n")
        jobFile.write("cd " + workDir + "\n")
        jobFile.write("eval `scramv1 runtime -sh` \n \n")

        jobFile.write("root -l -b -q '" + workDir + "/runNanoFakes.C(\"" + year + "\", \"" + job + "\")' \n \n")
        jobFile.close()
        
        subFile = open(subFileName, "w+")
        subFile.write('executable = '+jobFileName+'\n')
        subFile.write('universe = vanilla\n')
        subFile.write('output = '+ outFileName +'\n')
        subFile.write('error = '+ errFileName +'\n')
        subFile.write('log = '+ logFileName +'\n')
        subFile.write('+JobFlavour  = '+ queue +'\n')
        subFile.write('queue \n')
        subFile.close()
        
        if not job in jobsList:
            jobsList.append(job)

    completeJobFile = open(outputDir+"all.sub", "w+")    
    completeJobFile.write('executable = '+outputDir+'$(job).sh \n')
    completeJobFile.write('universe = vanilla \n')
    completeJobFile.write('output = '+outputDir+'$(job).out \n')
    completeJobFile.write('error = '+outputDir+'$(job).err \n')
    completeJobFile.write('log = '+outputDir+'$(job).log \n')
    completeJobFile.write('+JobFlavour  = '+ queue +'\n')
    completeJobFile.write('queue job in (\n')
    for job in jobsList:
        if job != "" and job != "\n":
            completeJobFile.write(job + '\n')
    completeJobFile.write(')\n')
    #completeJobFile.write('queue job from '+inputFile)
    completeJobFile.close()

    if doNotSend == 0:
        #print outputDir
        os.system("condor_submit " + outputDir + "all.sub")
        print "Done! "+ str(len(jobs)) +" jobs have been submitted. \n"        
    else:
        print "Done! However, the jobs have not been sent to the queue. \n"

if __name__ == "__main__":
    submit()
