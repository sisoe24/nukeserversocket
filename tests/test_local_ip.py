import random
import configparser


from src.widgets import ConnectionsWidget

LOCAL_IP = '192.168.1.%s' % random.randint(10, 99)


def test_local_ip_widget_entry(startup_no_settings):
    """Test if `local_ip` widget is writable and write something to it."""
    widget = ConnectionsWidget()
    widget.sender_mode.toggle()

    local_ip_entry = widget.ip_entry
    assert not local_ip_entry.isReadOnly()

    local_ip_entry.setText(LOCAL_IP)


def test_send_local_ip(tmp_settings_file):
    """Check if `local_ip` is saved correctly in settings.ini."""

    config = configparser.ConfigParser()
    config.read(tmp_settings_file)

    settings_values = config['server']['send_to_address']
    assert settings_values == LOCAL_IP
