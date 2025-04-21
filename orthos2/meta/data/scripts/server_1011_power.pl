#!/usr/bin/perl
use strict;
use warnings;
use threads;
use threads::shared;
use IO::Socket;
use IO::Select;
use Net::Ping;
use Net::Telnet;
use Getopt::Long;
use Net::DNS::Resolver;

use constant VERSION => "0.4";
use constant TRUE    => 1;
use constant FALSE   => 0;

# mode
use constant NO_MODE    => 0;
use constant LIST       => 1;
use constant FIND       => 2;
use constant BOOT       => 3;
use constant TURN_ON    => 4;
use constant TURN_OFF   => 5;
use constant HELP       => 6;

my ($mode, $host, $use_udp);

# method
my $searchmethods = 0;
use constant IPMI       => 1<<0;
use constant RPOWER     => 1<<1;
use constant WEB        => 1<<2;
use constant ILO        => 1<<3;
use constant ALL        => IPMI|WEB|RPOWER|ILO;

my $user = "user";         # rpower5 web username
my $pass = "pass";        # rpower5 web password
my $ilouser = "reboot";     # username for all iLOs
my $ilopass = "password";   # password for all iLOs
my $rackcount = 2;          # used racks on rpower5
my $debug = FALSE;          # print debugging output?

# hostnames
my @rpower_telnet = (
    'rpower1',
    'rpower2',
    'rpower3',
    'rpower4'
);

my $rpower_web = (
    'rpower5'
);

# hardcoded list of machines and their iLO (Hewlett Packard)
# TODO: make that dynamic!
my %ilos = (
    'machine'      => 'iLo'
);

# arrays:
#   IPMI array      [0] : hostname
#   ILO array       [0] : hostname
#                   [1] : iLO
#   rpower array    [0] : hostname
#                   [1] : rpower*
#                   [2] : rpower plug
#   rpower5 array   [0] : hostname
#                   [1] : rpower5 rack
#                   [2] : rpower5 plug

my @peers_ipmi    : shared;
my @peers_rpower  : shared;
my @peers_rpower5 : shared;
my @peers_ilo     : shared;

#
# --------------------------------------------------------------------------------------------------
sub show_usage {
    print "query_power v". VERSION ."\n\n";
    print "usage:\n";
    print "  -l             list all available ipmi machines\n";
    print "  -f   <host>    check if machine is available\n";
    print "  -b   <host>    reboot machine\n";
    print "  -on  <host>    switch machine on\n";
    print "  -off <host>    switch machine off\n";
    print "  -u             use UDP magic packet instead of ping to discover hosts\n";
    print "\n";
    print "  -i             IPMI only\n";
    print "  -I             iLO only\n";
    print "  -r             rpower only\n";
    print "  -w             rpower5 only\n";
    print "\n";
    print "  -d             Print debug messages\n";
    print "  -h             this usage message\n";
}

#
# --------------------------------------------------------------------------------------------------
sub system_print($) {
    my $cmd = shift;

    if ($debug) {
        print "Executing command =${cmd}=\n";
    }
    return system($cmd);
}

#
# --------------------------------------------------------------------------------------------------
sub machine2sp {
    my $address = shift;

    unless ($address =~ /\d+\.\d+\.\d+\.\d/) {
        my $packed = gethostbyname($host)
            or die "Couldn't resolve address for $host: $!\n";
        $address = inet_ntoa($packed);
    }
    my (@parts) = split(/\./, $address);

    # already SP
    if ($parts[2] == 5 || $parts[2] == 6) {
        return $address;
    }

    $parts[2] += 5;
    return join(".", @parts);
}

#
# --------------------------------------------------------------------------------------------------
sub sync_peer_list {
    my $host = shift;

    # use threads for faster searches
    my $powerswitch_telnet;
    my $powerswitch_http;
    my $ipmi_thread;
    my $ilo_thread;

    if ($searchmethods & ILO) {
        $ilo_thread = threads->new(\&list_ilo_peers);
    }
    if ($searchmethods & WEB) {
        $powerswitch_http = threads->new(\&list_rpower_web_peers);
    }
    if ($searchmethods & RPOWER) {
        $powerswitch_telnet = threads->new(\&list_powerswitch_peers);
    }
    if ($searchmethods & IPMI) {
        if(defined($host)) {
            $ipmi_thread = threads->new(\&find_ipmi_peer, $host);
        } else {
            $ipmi_thread = threads->new(\&list_ipmi_peers);
        }
    }

    if ($searchmethods & ILO) {
        $ilo_thread->join();
    }
    if ($searchmethods & WEB) {
        $powerswitch_http->join();
    }
    if ($searchmethods & RPOWER) {
        $powerswitch_telnet->join();
    }
    if ($searchmethods & IPMI) {
        $ipmi_thread->join();
    }
}

#
# --------------------------------------------------------------------------------------------------
sub print_host_list_columns {
    my $i = 0;

    print "\nIPMI machines\t\trpower1-4 machines\trpower5 machines\tiLO\n\n";
    while (defined($peers_ipmi[$i]) ||
            defined($peers_rpower[$i+($i)]) ||
            defined($peers_rpower5[$i+($i*2)]) ||
            defined($peers_ilo[$i+($i*2)])) {
    
        (defined($peers_ipmi[$i]) and
            printf("%-15s\t\t", $peers_ipmi[$i])) or print "\t\t\t";
        (defined($peers_rpower[$i+($i*2)]) and
            printf("%-15s\t\t", $peers_rpower[$i+($i*2)])) or print "\t\t\t";
        (defined($peers_rpower5[$i+($i*2)]) and
            printf("%-15s\t\t", $peers_rpower5[$i+($i*2)])) or print "\t\t\t";
        (defined($peers_ilo[$i+($i)]) and
            printf("%-15s\t\t", $peers_ilo[$i+($i)])) or print "\t\t\t";

        print "\n";
        $i++;
    }
}

#
# --------------------------------------------------------------------------------------------------
sub print_host_list_normal {
    for (my $i = 0; $i <= $#peers_ipmi; $i++) {
        print $peers_ipmi[$i] . "\n";
    }
    for (my $i = 0; $i <= $#peers_rpower; $i += 3) {
        print $peers_rpower[$i] . "\n";
    }
    for (my $i = 0; $i <= $#peers_rpower5; $i += 3) {
        print $peers_rpower5[$i] . "\n";
    }
}

#
# --------------------------------------------------------------------------------------------------
sub print_host_list {

    if (-t STDOUT) {
        print_host_list_columns();
    } else {
        print_host_list_normal();
    }
}

#
# --------------------------------------------------------------------------------------------------
sub search_host_list {
    my $host = shift;
    my $found = 0;
    my $i = 0;

    while (defined($peers_ipmi[$i]) ||
            defined($peers_rpower[$i+($i*2)]) ||
            defined($peers_rpower5[$i+($i*2)]) ||
            defined($peers_ilo[$i+($i)])) {
        if (defined($peers_ipmi[$i]) && ($host eq $peers_ipmi[$i])) {
            print "$host is available through IPMI\n";
            $found |= $found | IPMI;
        } elsif (defined($peers_rpower[$i+($i*2)]) && ($host eq $peers_rpower[$i+($i*2)])) {
            print "$host is available through $peers_rpower[$i+($i*2)+1] on port $peers_rpower[$i+($i*2)+2]\n";
            $found |= RPOWER;
        } elsif (defined($peers_rpower5[$i+($i*2)]) && ($host eq $peers_rpower5[$i+($i*2)])) {
            print "$host is available through rpower5 rack $peers_rpower5[$i+($i*2)+1] on port $peers_rpower5[$i+($i*2)+2]\n";
            $found |= WEB;
        } elsif (defined($peers_ilo[$i+($i)]) && ($host eq $peers_ilo[$i+($i)])) {
            print "$host is available through ilo on $peers_ilo[$i+($i)+1]\n";
            $found |= ILO;
        }
        $i++;
    }

    return $found;
}

#
# --------------------------------------------------------------------------------------------------
sub reboot {
    my $host = shift;
    my $where = 0;
    my $i;

    if(defined($host)) {
        $where = search_host_list($host);
        if ($where & ILO) {
            $i = 0;
            my $session = new Net::Telnet (Timeout => 5, Errmode => 'return');
            while(defined($peers_ilo[$i])) {
                if($peers_ilo[$i] eq $host) {
                    print "trying to reboot machine through $peers_ilo[$i+1]\n";
                    $session->open($peers_ilo[$i+1]);

                    # username
                    $session->waitfor(".*Login Name:.*");
                    $session->print("$ilouser");

                    # password
                    $session->waitfor(".*Password:.*");
                    $session->print("$ilopass");

                    # reboot
                    $session->cmd("power reset");

                    $session->close();
                    return TRUE;
                }
                $i+=2;
            }
        } elsif($where & IPMI) {
            print "trying to reboot machine through IPMI\n";
            if (system_print("ipmitool -I lan -H $host-sp -U user -P pass ".
                        "chassis power reset &>/dev/null") == 0) {
                return TRUE;
            }
            print "can't reboot $host trough IPMI\n";
        } elsif ($where & RPOWER) {
            $i = 0;
            my $session = new Net::Telnet(Timeout => 10,
                                          Errmode => 'return',
                                          Prompt => '/NPS> /');
            while(defined($peers_rpower[$i])) {
                if($peers_rpower[$i] eq $host) {
                    print "trying to reboot machine through $peers_rpower[$i+1]\n";
                    $session->open($peers_rpower[$i+1]);
                    $session->waitfor('/Enter Password:/');
                    $session->print($pass);
                    $session->waitfor('/NPS> /');
                    $session->print('/boot ' . $peers_rpower[$i+2]);
                    $session->waitfor('Sure? /');
                    $session->print('y');
                    $session->cmd("/X");
                    $session->waitfor('Sure? /');
                    $session->print('y');
                    $session->close();
                    return TRUE;
                }
                $i+=3;
            }
        }  elsif ($where & WEB) {
            $i = 0;
            while(defined($peers_rpower5[$i])) {
                if($peers_rpower5[$i] eq $host) {
                    print "trying to reboot machine through rpower5\n";
                    my $cmdstr;
                    
                    $cmdstr = "curl -i ";
                    $cmdstr .= "http://$rpower_web.domain.tld/rack$peers_rpower5[$i+1].html ";
                    $cmdstr .= "-u $user:$pass -d P$peers_rpower5[$i+1]$peers_rpower5[$i+2]=r 2>&1";
                    qx#$cmdstr#;
                    sleep(2);
                    my $result = qx#$cmdstr#;
                    if ($result =~ /303/g) {
                        return TRUE;
                    }
                    
                    print "can't reboot $host trough rpower5\n";
                }
                $i+=3;
            }
        }
        print "can't reboot $host at all.\n";
    } else {
        show_usage();
    }

    return FALSE;
}

#
# --------------------------------------------------------------------------------------------------
sub boot {
    my $host = $_[0];
    my $where = 0;
    my $i;

    if (defined($host)) {
        $where = search_host_list($host);
        if ($where & ILO) {
            $i = 0;
            my $session = new Net::Telnet (Timeout => 5, Errmode => 'return');
            while(defined($peers_ilo[$i])) {
                if($peers_ilo[$i] eq $host) {
                    print "trying to reboot machine through $peers_ilo[$i+1]\n";
                    $session->open($peers_ilo[$i+1]);

                    # username
                    $session->waitfor(".*Login Name:.*");
                    $session->print("$ilouser");

                    # password
                    $session->waitfor(".*Password:.*");
                    $session->print("$ilopass");

                    # reboot
                    $session->cmd("power on");

                    $session->close();
                    return TRUE;
                }
                $i+=2;
            }
        } elsif ($where & IPMI) {
            print "trying to boot machine through IPMI\n";
            if (system_print("ipmitool -I lan -H $host-sp -U root -P pass ".
                        "chassis power on &>/dev/null") == 0) {
                return TRUE;
            }
            print "can't boot $host trough IPMI\n";
        } elsif ($where & RPOWER) {
            $i = 0;
            my $session = new Net::Telnet (Timeout => 5, Errmode => 'return');
            while(defined($peers_rpower[$i])) {
                if($peers_rpower[$i] eq $host) {
                    print "trying to boot machine through $peers_rpower[$i+1]\n";
                    $session->open($peers_rpower[$i+1]);
                    $session->print("pass");
                    $session->cmd("/on $peers_rpower[$i+2]");
                    $session->cmd("Y");
                    $session->cmd("/X");
                    $session->cmd("Y");
                    $session->close();
                    return TRUE;
                }
                $i+=3;
            }
        } elsif ($where & WEB) {
            $i = 0;
            while(defined($peers_rpower5[$i])) {
                if($peers_rpower5[$i] eq $host) {
                    print "trying to boot machine through rpower5\n";

                    my $cmdstr;
                    $cmdstr = "curl -i ";
                    $cmdstr .= "http://$rpower_web.domain.tld/rack$peers_rpower5[$i+1].html ";
                    $cmdstr .= "-u $user:$pass -d P$peers_rpower5[$i+1]$peers_rpower5[$i+2]=1 2>&1";
                    qx#$cmdstr#;
                    sleep(2);
                    my $result = qx#$cmdstr#;
                    if ($result =~ /303/g) {
                        return TRUE;
                    }
                    print "can't boot $host trough rpower5\n";
                }
                $i+=3;
            }
        }
        print "can't boot $host at all.\n";
    } else {
            show_usage();
    }
    return FALSE;
}

#
# -----------------------------------------------------------------------------
sub halt {
    my $host = shift;
    my $where = 0;
    my $i;

    if (defined($host)) {
        $where = search_host_list($host);
        if ($where & ILO) {
            $i = 0;
            my $session = new Net::Telnet (Timeout => 5, Errmode => 'return');
            while(defined($peers_ilo[$i])) {
                if($peers_ilo[$i] eq $host) {
                    print "trying to reboot machine through $peers_ilo[$i+1]\n";
                    $session->open($peers_ilo[$i+1]);

                    # username
                    $session->waitfor(".*Login Name:.*");
                    $session->print("$ilouser");

                    # password
                    $session->waitfor(".*Password:.*");
                    $session->print("$ilopass");

                    # reboot
                    $session->cmd("power off");

                    $session->close();
                    return TRUE;
                }
                $i+=2;
            }
        } elsif ($where & IPMI) {
            print "trying to shutdown machine through IPMI\n";
            if (system_print("ipmitool -I lan -H $host-sp -U user -P pass ".
                        "chassis power off &>/dev/null") == 0) {
                return TRUE;
            }
            print "can't shutdown $host trough IPMI\n";
        } elsif ($where & RPOWER) {
            $i = 0;
            my $session = new Net::Telnet (Timeout => 5, Errmode => 'return');
            while(defined($peers_rpower[$i])) {
                if($peers_rpower[$i] eq $host) {
                    print "trying to shutdown machine through $peers_rpower[$i+1]\n";
                    $session->open($peers_rpower[$i+1]);
                    $session->print("pass");
                    $session->cmd("/off $peers_rpower[$i+2]");
                    $session->cmd("Y");
                    $session->cmd("/X");
                    $session->cmd("Y");
                    $session->close();
                    return TRUE;
                }
                $i+=3;
            }
        } elsif ($where & WEB) {
            $i = 0;
            while(defined($peers_rpower5[$i])) {
                if($peers_rpower5[$i] eq $host) {

                    my $cmdstr;
                    $cmdstr = "curl -i ";
                    $cmdstr .= "http://$rpower_web.domain.tld/rack$peers_rpower5[$i+1].html ";
                    $cmdstr .= "-u $user:$pass -d P$peers_rpower5[$i+1]$peers_rpower5[$i+2]=0 2>&1";
                    qx#$cmdstr#;
                    sleep(2);
                    my $result = qx#$cmdstr#;
                    if ($result =~ /303/g) {
                        return TRUE;
                    }
                    print "can't shutdown $host trough rpower5\n";
                }
                $i+=3;
            }
        }
        print "can't shutdown $host at all.\n";
    } else {
        show_usage();
    }

    return FALSE;
}

#
# -----------------------------------------------------------------------------
sub find_ipmi_peer_udp {
    my $buffer;
    my $select = new IO::Select;
    my $host = shift;
    my $ret = 0;

    $host = machine2sp($host);
    my $socket = new IO::Socket::INET->new(
        PeerAddr => $host,
        PeerPort => '623',
        Proto    => 'udp',
        Timeout  => 5,
    ) or die("Unable to open connection: $!\n");

    $socket->send("\x06\x00\xFF\x06\x00\x00\x11\xbe\x80\x00\x00\x00");

    $select->add( $socket );
    while ($select->can_read(2)) {
        $socket->recv($buffer, 4096);
    }

    return defined($buffer) && $buffer ne "";
}

#
# -----------------------------------------------------------------------------
sub find_ipmi_peer_ping {
    my $host = shift;
    my $ret;

    my $ping = Net::Ping->new('udp', 1);
    $ret = $ping->ping(machine2sp($host));
    $ping->close();

    return $ret;
}

#
# -----------------------------------------------------------------------------
sub find_ipmi_peer {
    my $ret;
    my $host = shift;

    if ($use_udp) {
        $ret = find_ipmi_peer_udp($host);
    } else {
        $ret = find_ipmi_peer_ping($host);
    }

    if ($ret) {
        @peers_ipmi = $host;
    }

    return $ret;
}

#
# -----------------------------------------------------------------------------
sub strip_domain {
    my $fqdn = shift;
    return ($fqdn =~ /^([-a-zA-Z0-9]+)\.?/)[0];
}

#
# -----------------------------------------------------------------------------
sub list_ipmi_peers_udp {
    my $clientIP;
    my $query;
    my $select = new IO::Select;
    my $resolver = Net::DNS::Resolver->new;

    my $socket = new IO::Socket::INET->new(
        PeerAddr => inet_ntoa(INADDR_BROADCAST),
        PeerPort => '623',
        Proto    => 'udp',
        Broadcast => 1,
        LocalPort => '65123',
        ReuseAddr => 1,
        MultiHomed => 1,
    ) or die("Unable to open connection: $!\n");

    $socket->send("\x06\x00\xFF\x06\x00\x00\x11\xbe\x80\x00\x00\x00");
    $socket->close;

    my $recv_socket = new IO::Socket::INET->new(
        LocalPort => '65123',
        Proto    => 'udp',
        ReuseAddr => 1,
        MultiHomed => 1,
    ) or die("Unable to open connection: $!\n");

    $select->add( $recv_socket );
    while( $select->can_read(10) ) {
        $recv_socket->recv(my $buffer, 1);

        $clientIP = $recv_socket->peerhost();
        $query = $resolver->search("$clientIP");
        if ($query) {
            foreach ($query->answer) {
                next unless $_->type eq "PTR";
                push(@peers_ipmi, strip_domain($_->ptrdname));
            }
        } else { print "$clientIP,",$resolver->errorstring,"\n"; }
    }

    $recv_socket->close;
}

#
# -----------------------------------------------------------------------------
sub list_ipmi_peers_ping {
    my $clientIP;
    my ($a, $b);

    open FH, "-|", "nmap -T4 -sP 10.11.5-6.* -r 2>/dev/null"
        or die "Could not start nmap: $!";

    while (<FH>) {
        if (/^Host.*appears to be up./) {
            my ($hostname, $ip) =
                    /^Host (\S+) \(([()0-9\.]+)\) appears to be up./;
            push(@peers_ipmi, strip_domain($hostname));
        }
    }

    close FH;
}

#
# -----------------------------------------------------------------------------
sub list_ipmi_peers {
    my $clientIP;
    my ($a, $b);

    if ($use_udp) {
        list_ipmi_peers_udp();
    } else {
        list_ipmi_peers_ping();
    }
}

#
# -----------------------------------------------------------------------------
sub list_ilo_peers {
    @peers_ilo = (%ilos);
}

#
# -----------------------------------------------------------------------------
sub list_powerswitch_peers {
    my @lines;
    my $rpower_host;
    my $session = new Net::Telnet (Timeout => 5, Errmode => 'return');

    foreach $rpower_host (@rpower_telnet) {
        $session->open($rpower_host);
        $session->print("pass");
        @lines = $session->cmd("/S");
        foreach(@lines) {
            if( $_ =~ /(\d+)\s*\| ([^\s]+)\s*\|.*/g ) {
                if( $2 ne "-" ) {
                    push(@peers_rpower, ($2, $rpower_host, $1));
                }
            }
        }
        $session->cmd("/X");
        $session->cmd("Y");
        $session->close();
    }
    return 1;
}

# -----------------------------------------------------------------------------
sub list_rpower_web_peers {
    my $hostlist;
    my $port;
    my $i;

    for ($i=1; $i <= $rackcount; $i++) {
        $port = 1;
        $hostlist = qx#wget -q -O - http://$user:$pass\@$rpower_web.network.tld/rack$i.html#;
        while ($hostlist =~ /\"([^\s\"]+)\s+\",(\d+)\s+,/g) {
            push (@peers_rpower5, ($1, $i, $port));
            $port++;
        }
        if ($hostlist eq "") {
            $i--;
        }
    }
}


#
# ----------- MAIN ------------------------------------------------------------
#

if (-t STDOUT) {
    print STDERR "WARNING: Direct use of query_power.pl is DEPRECATED. Use orthos for this task!\n";
}

GetOptions(
    "list|l"        => sub {
                            $mode = LIST
                       },
    "h|help"        => sub {
                            $mode = HELP;
                       },
    "f|find=s"      => sub {
                            $host = $_[1];
                            $mode = FIND;
                       },
    "b|reboot=s"    => sub {
                            $host = $_[1];
                            $mode = BOOT;
                       },
    "on=s"          => sub {
                            $host = $_[1];
                            $mode = TURN_ON;
                       },
    "off=s"         => sub {
                            $host = $_[1];
                            $mode = TURN_OFF;
                       },
    "w|web",        => sub {
                            $searchmethods |= WEB;
                       },
    "i|ipmi",       => sub {
                            $searchmethods |= IPMI;
                       },
    "r|rpower",     => sub {
                            $searchmethods |= RPOWER;
                       },
    "I|ilo",        => sub {
                            $searchmethods |= ILO;
                       },
    "d|debug",      => sub {
                            $debug = TRUE;
                       },
    "u|udp",        \$use_udp
);

if (!defined $mode) {
    show_usage();
    exit 1;
}
if ($mode == HELP) {
    show_usage();
    exit 0;
}

if (defined $host) {
    $host =~ s/\.arch\.suse\.de$//;
}

if ($searchmethods == 0) {
    $searchmethods = ALL;
}

if ($mode == LIST) {
    sync_peer_list();
    print_host_list();
}
if ($mode == FIND) {
    sync_peer_list($host);
    my $found = search_host_list($host);
    exit($found ? 0 : 1);
}
my $retcode = 0;
if ($mode == TURN_OFF) {
    sync_peer_list($host);
    if (!halt($host)) {
        $retcode += 1;
    }
}
if ($mode == TURN_ON) {
    sync_peer_list($host);
    if (!boot($host)) {
        $retcode += 1;
    }
}
if ($mode == BOOT) {
    sync_peer_list($host);
    if (!reboot($host)) {
        $retcode += 1;
    }
}

exit($retcode);

# vim: set sw=4 ts=4 et: :collapseFolds=1:maxLineLen=100:
