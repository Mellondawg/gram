from GenericInstaller import GenericInstaller

# We assume at this point that these have been completed:
# steps #1 (install Ubuntu) and #3 (configure the network)
# and reboot
class OperatingSystem(GenericInstaller):

    # Return a list of command strings for installing this component
    def installCommands(self, params):
        self.comment("*** OperatingSystem Install ***")
        self.comment("Step 2. Add repository and upgrade Ubuntu")
        self.add("apt-get install -y python-software-properties")
        self.add('add-apt-repository -y ppa:openstack-ubuntu-testing/folsom-trunk-testing')
        self.add('add-apt-repository -y ppa:openstack-ubuntu-testing/folsom-deps-staging')
        self.add('apt-get update && apt-get -y dist-upgrade')

        self.comment("Set up ubuntu cloud keyring")
        self.writeToFile('deb http://ubuntu-cloud.archive.canonical.com/ubuntu precise-updates/folsom main', 
                         '/etc/apt/sources.list.d/folsom.list')
        self.aptGet('ubuntu-cloud-keyring')

        self.comment("Enable IP forwarding")
        self.sed('s/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/',
                 '/etc/sysctl.conf')
        self.add("sysctl net.ipv4.ip_forward=1")
        self.add('service networking restart')

        self.comment("Step 4: Configure NTP")
        self.aptGet("ntp")
        self.appendToFile('Use Ubuntu ntp server as fallback.',
                          '/etc/ntp.conf')
        self.appendToFile('server ntp.ubuntu.com iburst', 
                          '/etc/ntp.conf')
        self.appendToFile('server 127.127.1.0','/etc/ntp.conf')
        self.appendToFile('fudge 127.127.1.0 stratum 10', 
                          '/etc/ntp.conf')
        self.add('service ntp restart')


    # Return a list of command strings for uninstalling this component
    def uninstallCommands(self, params):
        self.comment("*** OperatingSystem Uninstall ***")
        self.aptGet("ntp", True)

