# copyright, 2015 Hewlett-Packard Development Company, LP

# testing
# https://github.com/srsakhamuri/ceilometer-tools/blob/master/make_test_data2.py
# https://github.com/srsakhamuri/ceilometer-tools/blob/master/send_test_data.py
# python ./send_test_data.py --counter meter1 --samples-count 100 --resources_count 10 --topic metering

#    R e p o r t    C e i l o m e t e r    C o u n t e r s

use strict;

# Allow reference to collectl variables, but be CAREFUL as these should be treated as readonly
our ($intSecs, $hiResFlag, $SEP, $rate, $miniDateTime, $miniFiller);
our ($datetime, $showColFlag, $playback, $verboseFlag, $export);

# internal globals
my $version='1.0';
my ($debug, $options);
my ($alarm, $collector, $eval, $notify, $filter);
my (%data, %tot, %totTOT);

my %logfile;
$logfile{api}-> {name}='/var/log/ceilometer/stats-api';
$logfile{alrm}->{name}='/var/log/ceilometer/stats-alarm-notifier';
$logfile{coll}->{name}='/var/log/ceilometer/stats-collector';
$logfile{eval}->{name}='/var/log/ceilometer/stats-alarm-evaluator';
$logfile{noti}->{name}='/var/log/ceilometer/stats-agent-notification';

$logfile{api}->{opened}=0;
$logfile{alrm}->{opened}=$logfile{coll}->{opened}=0;
$logfile{eval}->{opened}=$logfile{noti}->{opened}=0;

sub ceilInit
{
  my $impOptsref=shift;
  my $impKeyref= shift;

  error("ceil must be called with --import NOT --export")     if $export=~/ceil/;

  $debug=0;
  $filter='';
  my $versionFlag=0;
  if (defined($$impOptsref))
  {
    foreach my $option (split(/,/,$$impOptsref))
    {
      my ($name, $value)=split(/=/, $option);
      error("invalid option: '$name'")    if $name !~/^[dfhv]$/;
      $debug=$value       if $name=~/d/ && defined($value);
      $filter=$value      if $name=~/f/;
      $versionFlag=1      if $name=~/v/;
      ceilHelp()          if $name=~/h/;
    }
  }

  if ($versionFlag)
  {
    print "ceil v$version\n";
    exit(0);
  }

  foreach my $logType (keys %logfile)
  { $data{$logType}={}; }

  $$impOptsref='s';    # only summary data
  $$impKeyref='ceil';
  return(1);
}

# Anything you might want to add to collectl's header.  
sub ceilUpdateHeader
{
}

sub ceilInitInterval
{
  for my $type (keys %logfile)
  { $tot{$type}=0; }
}

sub ceilGetData
{
  # rare that the logs aren't aleady open other than during initial pass,
  # perhaps at system startup
  foreach my $type (keys %logfile)
  {
    if (!$logfile{$type}->{opened})
    {
      if ($debug & 1)
      { print "Open: $logfile{$type}->{name}\n"; }
      open $logfile{$type}->{fd}, "<$logfile{$type}->{name}";
      $logfile{$type}->{opened}=1;
    } 
 
    # but only if successfully opened
    if ($logfile{$type}->{opened})
    {
      my $fd=$logfile{$type}->{fd};
      seek($fd, 0, 0);
      while (my $line=<$fd>)
      {
        if (defined($line))
        {
          next    if $line=~/^#/;
	  record(2, "ceil:$type $line");
        }
      }
    }
  }
}

sub ceilAnalyze
{
  my $type=shift;    # not used
  my $dataref=shift;

  my $logType=(split(/:/, $type))[1];
  $$dataref=~s/[{}]//g;    # get rid of surrounding {}s
  foreach my $pair (split(/, /, $$dataref))
  {
    my ($name, $val)=split(/: /, $pair);
    $name=~s/'//g;
    print "Name: $name  VAL: $val  Filter: $filter\n"    if $debug & 1;

    next    if $filter ne '' && $name!~/$filter/;
    #print "PASSED: $name  VAL: $val\n";

    $data{$logType}->{$name}->{last}=0    if !defined($data{$logType}->{$name}->{last});
    $data{$logType}->{$name}->{now}=$val-$data{$logType}->{$name}->{last};
    $data{$logType}->{$name}->{last}=$val;

    $tot{$logType}+=$data{$logType}->{$name}->{now};
  }
}

sub ceilPrintBrief
{
  my $type=shift;
  my $lineref=shift;

  if ($type==1)       # header line 1
  {
    $$lineref.="<--Ceilometer-->";
  }
  elsif ($type==2)    # header line 2
  {
    $$lineref.="  Api Alrm Coll Eval Noti";
  }
  elsif ($type==3)    # data
  {
    # only way to guarantee print order
    foreach my $logType ('api', 'alrm', 'coll', 'eval', 'noti')
    { $$lineref.=sprintf(" %4d", $tot{$logType}/$intSecs); }
  }
  elsif ($type==4)    # reset 'total' counters
  {
    foreach my $type (keys %logfile)
    { $totTOT{$type}=0; }
  }
  elsif ($type==5)    # increment 'total' counters
  {
    foreach my $logType (keys %logfile)
    { $totTOT{$logType}+=$tot{$logType}; }
  }
  elsif ($type==6)    # print 'total' counters
  {
    print " ";
    foreach my $logType ('api', 'alrm', 'coll', 'eval', 'noti')
    { printf "%4d ", $totTOT{$logType}; }
  }
}

sub ceilPrintVerbose
{
  my $printHeader=shift;
  my $homeFlag=   shift;
  my $lineref=    shift;
}

sub ceilPrintPlot
{
  my $type=   shift;
  my $ref1=   shift;

  if ($type==1)
  {
    $$ref1.="[CEIL]Api${SEP}[CEIL]Alrm${SEP}[CEIL]Coll${SEP}[CEIL]Eval${SEP}[CEIL]Noti${SEP}";
  }
  else
  {
    $$ref1.=sprintf("$SEP%d$SEP%d$SEP%d$SEP%d$SEP%d",
        $tot{api}, $tot{alrm}, $tot{coll}, $tot{eval}, $tot{noti});
  }
}

sub ceilPrintExport
{
  my $type=shift;
  my $ref1=shift;
  my $ref2=shift;
  my $ref3=shift;
  my $ref4=shift;
  my $ref5=shift;
  my $ref6=shift;
}

sub ceilHelp
{
  my $help=<<CEILEOF;

usage: ceil, switches...

CEILEOF

  print $help;
  exit(0);
}

1;

