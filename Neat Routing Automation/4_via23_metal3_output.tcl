# Auto-generated Via23 and Metal3 creation script
# Generated from Via12 positions
# Window Number: 2
# Device X Range: 3.723 to 6.535 microns
# Via23 X Range: 4.123 to 6.135 microns
# X Step: 0.000 microns
# Via Name: VIA23

# ========== Net: Vb ==========
# X Position: 4.123 microns
# Y Positions (1): ['5.941']

# Via23 at Y=5.941
ile::createVia
gi::setField {viaDefName} -value {VIA23} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.123 5.941} -context [db::getNext [de::getContexts -window 2]]

# Metal3 Rectangle
le::createRectangle {{4.083 5.941} {4.163 6.441}} -design [ed] -lpp {M3 drawing} -net Vb

