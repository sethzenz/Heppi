#!/usr/bin/python

import ROOT # needed
import os, sys, glob, sys, json
import logging
from   rootpy.tree import Cut  # more robust
import colors 
from rootpy.interactive import wait

samples     = {}
variables   = {}
rootfile    = {}
cutflow     = [] ## save all the cuts
selections  = {}

# delete me
sampledir   = './data/' ## temp variable
treename    = 'VBFMVADumper/trees/*_13TeV_VBFDiJet'
options     = None   
allnormhist = False
# =================================================
# plot decoration
def draw2Legend(histo1,
                histo2,
                label1,
                label2):
    legend = ROOT.TLegend(0.5, 0.75,
                          (1.00 - ROOT.gStyle.GetPadRightMargin()),
                          (0.99 - ROOT.gStyle.GetPadTopMargin()))
    legend.SetTextAlign( 12 )
    legend.SetTextFont ( 42 )
    legend.SetTextSize ( 0.04 )
    legend.SetLineColor( 0 )
    legend.SetLineColorAlpha(0,0)
    legend.SetShadowColor(0)
    
    entry1 = legend.AddEntry( histo1, label1, "f" );
    entry2 = legend.AddEntry( histo2, label2, "f" );
    
    legend.SetFillColor( 0 );
    legend.SetFillStyle( 0 );
    legend.Draw();
# =================================================
def read_plotcard(plotcard):
    config = json.loads(open(plotcard).read())
    for key in config:
        if 'variables' in key:
            logging.debug(' ---- book variables ----')
            for var in config[key]:
                logging.debug(' -- %17s  %12s ' % ( var ,config[key][var]['hist']))
                variables[var] = config[key][var]
        if 'processes' in key:
            logging.debug(' ---- book processes ----')
            for proc in config[key]:
                logging.debug(' -- %17s  %12s ' % (proc,  config[key][proc]))
                samples[proc] = config[key][proc]
                
        if 'selections' in key:
            logging.debug(' ---- book selections ---')
            for sel in config[key]:
                print
                logging.debug(' -- %17s  %12s ' % (sel , config[key][sel]))
                selections[sel] = config[key][sel]
            logging.debug(' -------------------')

# =================================================
def produce_histos(variable, selection='', options=[''] ,mode=''):
    """
    mode:
    
    [1] none : produce a list of histogram with with the corresponding collors. only the samples labeled 
    'signal' or 'spectator' will non-color filled
    the sample label 'data' will be drawn as doted points with error bars
    [2] stack :  this will produce a histogram (signal) and hstack with all the backround stacked, 
    as a third element a list of histogram with same order as in the hstack 
    [3] bkgadd : this add all the backgrounds in a same histogram, the function will then retrieve:
    the signal the spectator and background histogram
    
    options :
    
    options can be entred as a list:
    the list of options are : ['norm', '', ... ]
    """
    
    histos = {}
    hstack = ROOT.THStack('hs_' + variable,'')
    for proc in samples:
        flist = glob.glob( sampledir + '/*'+ samples[proc]['name'] +'*.root')
        roof  = ROOT.TFile.Open(flist[0])
        tree  = roof.Get(treename.replace('*',proc))
        tree.Project(
            'h_' + variable + variables[variable]['hist'],
            variable,
            selection
        )
        
        h = ROOT.gDirectory.Get('h_' + variable )
        h.SetDirectory(0)
        eventperbin = float(h.GetXaxis().GetXmax() - h.GetXaxis().GetXmin())/h.GetNbinsX()
        if 'signal' or 'spectator' in samples[proc]['label']:
            h.SetLineColor(samples[proc]['color'])
        else:
            h.SetFillColor(samples[proc]['color'])
            h.SetLineColor(ROOT.kBlack)
            h.SetTitle(";" + variables[variable]['title']+(";Entries/%1.1f"% eventperbin ))
        if 'norm' in options:
            integral = h.Integral()
            h.Scale(1.0/integral)
            h.GetYaxis().SetTitle("1/n dn/d"+variables[variable]['title'] +("/%1.1f" % eventperbin))

        if mode=='stack':
            if 'background' in samples[proc]['label']:
                hstack.Add(h);
            else:
                histos[variable].append(h)
            histos[variable].append(hstack)
        else :    
            histos[variable].append(h)
        
        
    return histos;


def draw_variable(variable, selection):
    hist = []
    sel=''

    histfilename = ('plots/histogram_' + selection + '_' + variable)
    print ' -- ', variable,'\t',variables[variable]
    # create a list of histogram for each process
    legend = ROOT.TLegend(0.5, 0.65,
                          (0.95 - ROOT.gStyle.GetPadRightMargin()),
                          (0.95 - ROOT.gStyle.GetPadTopMargin()))
    print ' --  cut flow', cutflow
    maximum=0;
    if selection in selections:
        sel = selections[selection]
        
    hstack = ROOT.THStack('hs_' + variable,'')
    hstack.SetName('hs_'+ variable)
    hstack.SetTitle(";" + variables[variable]['title']+";entries")
    for proc in samples:
        print '--', proc, ' ',samples[proc]
        flist = glob.glob( sampledir + '/*'+ samples[proc]['name'] +'*.root')
        roof  = ROOT.TFile.Open(flist[0])
        tree  = roof.Get(treename.replace('*',proc))
        print 'h_' + variable + variables[variable]['hist']
        print variable
        print sel
        if variables[variable]['norm'] == True or allnormhist==True:
            tree.Project(
                'h_' + variable + variables[variable]['hist'],
                variable,
                sel
            )
        else:
            seltmp = ''
            if sel =='':
                seltmp = 'weight'
            else:
                seltmp = 'weight*(' + sel + ')'
            tree.Project(
                'h_' + variable + variables[variable]['hist'],
                variable,
                seltmp
            )
        h = ROOT.gDirectory.Get('h_' + variable )
        h.SetDirectory(0)
        hcolor = 0
        for c in colors.usercolor:
            if c in proc:
                hcolor = colors.usercolor[c]
        legend.AddEntry( h, samples[proc]["title"], "f" );
        if ('signal' in samples[proc]['label']) or ('spectator' in samples[proc]['label']) or (variables[variable]['norm'] == True) or (allnormhist==True):
            h.SetLineColor(hcolor)
            h.SetTitle(";" + variables[variable]['title']+";entries")
        else:
            h.SetTitle(";" + variables[variable]['title']+";entries")
            
        print 'norm hist', allnormhist
        if variables[variable]['norm'] == True or allnormhist==True:
            integral = h.Integral()
            if integral==0:
                integral = 1.0;
            h.Scale(1.0/integral)
            maximum = max(maximum, h.GetMaximum())
            print '\t max here:', maximum
        else:
            h.SetLineColor(ROOT.kBlack)
            h.SetFillColor(hcolor)
            maximum = max(maximum, h.GetMaximum())
            hstack.Add(h);
        hist.append(h)
    print 'maximum ==', maximum     
    hist.sort(key = lambda x: x.GetEffectiveEntries())
    c = ROOT.TCanvas('c_'+variable,variable,600,700)
    c.cd()
    count = 0
    if variables[variable]['norm'] == True or allnormhist==True:
        for h in hist:
            print 'orderded histo::', h.GetName()
            if count==0:
                h.GetYaxis().SetRangeUser(0.000001,maximum+ maximum*0.5)
                h.Draw('hist')
            else:
                h.GetYaxis().SetRangeUser(0.000001,maximum+ maximum*0.5)
                h.Draw('hist,same')
            count = count+1
    else:
        htmp = h.Clone('h_clone')
        htmp.Clear()
        ymin = 0;
        ymax = hstack.GetMaximum()
        if  options.allloghist:
            ymin = 0.1
            ymax = 2000*ymax
        htmp.GetYaxis().SetRangeUser(ymin,ymax + ymax*0.5)
        htmp.Draw()
        hstack.Draw('hist,same')
        
    ROOT.gPad.RedrawAxis();
    if options.allloghist:
        ROOT.gPad.SetLogy()
        histfilename = histfilename + '_log'
        
    # this is for the legend
    legend.SetTextAlign( 12 )
    legend.SetTextFont ( 42 )
    legend.SetTextSize ( 0.03 )
    legend.SetLineColor( 0 )
    legend.SetFillColor( 0 )
    legend.SetFillStyle( 0 )
    legend.SetLineColorAlpha(0,0)
    legend.SetShadowColor(0)
    legend.Draw()
    
    if variables[variable]['norm']==True or allnormhist==True:
        histfilename = histfilename + '_norm'
    c.SaveAs( histfilename + '.png')
    c.SaveAs( histfilename + '.pdf')
    
    for h in hist:
        h.Delete()
    c.Clear()
    
# =================================================

#------------------------------------
#         main function 
#------------------------------------
from optparse import OptionParser

def get_options():
    parser = OptionParser()
    parser.add_option("-r", "--load", dest="plotcard",default='plotcard.json',
                      help="""
                      Load the plot card in json format, 
                      please use ./makeplotcard.py to create one
                      """,
                      metavar="FILE")
    parser.add_option("-t", "--tree", dest="treename",default='VBFMVADumper/*VBFDiJet',
                      help="dumper tree that you want to use", metavar="FILE")
    parser.add_option("-a", "--all", 
                      action="store_true", dest="draw_all", default=False,
                      help="draw all the variables specified in the plotcard")
    parser.add_option("-d", "--display", 
                      action="store_true", dest="display", default=False,
                      help="draw all the variables specified in the plotcard")
    parser.add_option("-v", "--variable",
                      dest="variable",default="dijet_leadPt",
                      help="name of the variable you want to draw")
    parser.add_option("-n", "--allnorm",
                      action="store_true",dest="allnormhist",default=False,
                      help="all the histogram will be normilised")
    parser.add_option("-l", "--alllog",
                      action="store_true",dest="allloghist",default=False,
                      help="all the histogram will be in log scale")
    return parser.parse_args()

if __name__ == "__main__":
    (opt, args) = get_options()
    options  = opt
    if opt.display :
        ROOT.gROOT.SetBatch(ROOT.kTRUE) 
    # reading the plotcard from json
    #logging.basicConfig(level=options.loglevel
    allnormhist = options.allnormhist
    
    ROOT.gROOT.ProcessLine(".x ~/.rootsys/rootlogon.C")
    read_plotcard(options.plotcard)
    
    for var in variables:
        draw_variable(var,'VBF')
    
    #hist = produce_histos('jet1_pt','',['norm'],'')
    #print 'voila ::',hist
    
