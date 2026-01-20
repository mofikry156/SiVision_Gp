# TCL Via23 and Metal3 Generation Script
# Auto-generated from Via12 database
# Window Number: 2
# X Start: 4.123 microns
# X Step: 0.287 microns
# Via Name: VIA23
# Device Y positions filtered: 7

# Via23 Configuration (one-time setup)
ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA23} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]

# ========== Net: V2 (X=4.123) ==========
# Found 4 unique Y position(s)
de::addPoint {4.123 6.957} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {4.123 7.525} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {4.123 7.645} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {4.123 8.213} -context [db::getNext [de::getContexts -window 2]]

# Metal3 Rectangle for V2
le::createRectangle {{4.083 6.957} {4.163 8.213}} -design [ed] -lpp {M3 drawing} -net V2

# ========== Net: VDD (X=4.410) ==========
# Found 4 unique Y position(s), filtered 2 (device Y match)
de::addPoint {4.410 8.785} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {4.410 9.791} -context [db::getNext [de::getContexts -window 2]]

# Metal3 Rectangle for VDD
le::createRectangle {{4.370 8.785} {4.450 9.791}} -design [ed] -lpp {M3 drawing} -net VDD

# ========== Net: VSS (X=4.698) ==========
# Found 6 unique Y position(s), filtered 5 (device Y match)
de::addPoint {4.698 6.383} -context [db::getNext [de::getContexts -window 2]]

# Metal3 Rectangle for VSS
le::createRectangle {{4.658 6.383} {4.738 6.883}} -design [ed] -lpp {M3 drawing} -net VSS

# ========== Net: Vb (X=4.985) ==========
# Found 1 unique Y position(s)
de::addPoint {4.985 6.027} -context [db::getNext [de::getContexts -window 2]]

# Metal3 Rectangle for Vb
le::createRectangle {{4.945 6.027} {5.025 6.527}} -design [ed] -lpp {M3 drawing} -net Vb

# ========== Net: Vin (X=5.273) ==========
# Found 4 unique Y position(s)
de::addPoint {5.273 6.871} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {5.273 7.439} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {5.273 7.731} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {5.273 8.299} -context [db::getNext [de::getContexts -window 2]]

# Metal3 Rectangle for Vin
le::createRectangle {{5.233 6.871} {5.313 8.299}} -design [ed] -lpp {M3 drawing} -net Vin

# ========== Net: Vout (X=5.560) ==========
# Found 6 unique Y position(s)
de::addPoint {5.560 6.698} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {5.560 7.266} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {5.560 7.904} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {5.560 8.472} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {5.560 8.970} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {5.560 9.608} -context [db::getNext [de::getContexts -window 2]]

# Metal3 Rectangle for Vout
le::createRectangle {{5.520 6.698} {5.600 9.608}} -design [ed] -lpp {M3 drawing} -net Vout

# ========== Net: net48 (X=5.848) ==========
# Found 5 unique Y position(s)
de::addPoint {5.848 6.283} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {5.848 6.513} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {5.848 7.081} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {5.848 8.087} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {5.848 8.655} -context [db::getNext [de::getContexts -window 2]]

# Metal3 Rectangle for net48
le::createRectangle {{5.808 6.283} {5.888 8.655}} -design [ed] -lpp {M3 drawing} -net net48

# ========== Net: net7 (X=6.135) ==========
# Found 8 unique Y position(s)
de::addPoint {6.135 6.597} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {6.135 7.165} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {6.135 7.987} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {6.135 8.555} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {6.135 8.869} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {6.135 9.143} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {6.135 9.435} -context [db::getNext [de::getContexts -window 2]]
de::addPoint {6.135 9.691} -context [db::getNext [de::getContexts -window 2]]

# Metal3 Rectangle for net7
le::createRectangle {{6.095 6.597} {6.175 9.691}} -design [ed] -lpp {M3 drawing} -net net7

# Total Via23 filtered (device Y match): 7
