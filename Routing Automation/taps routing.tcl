# Generated TCL script for tap routing
# Power net: VDD
# Ground net: VSS
# Window number: 2
#
# Configuration:
#   Rectangle X offsets: 0 to 147
#   Rectangle Y offsets: 106 to 140
#   Via X offsets: 110 to 45
#   Via Y offset: 123
#   Via spacing: 74
#   Via type: VIA12
#   Metal layer: M2

# ========== NTAP ROWS (Power) ==========
# Ntap Row at Y=9857
le::createRectangle {{3.723 9.963} {6.903 9.997}} -design [ed] -lpp {M2 drawing} -net VDD

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {3.833 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {3.907 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {3.981 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.055 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.129 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.203 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.277 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.351 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.425 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.499 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.573 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.647 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.721 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.795 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.869 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.943 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.017 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.091 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.165 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.239 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.313 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.387 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.461 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.535 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.609 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.683 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.757 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.831 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.905 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.979 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.053 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.127 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.201 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.275 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.349 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.423 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.497 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.571 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.645 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.719 9.980} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.793 9.980} -context [db::getNext [de::getContexts -window 2]]


# ========== PTAP ROWS (Ground) ==========
# Ptap Row at Y=5681
le::createRectangle {{3.723 5.787} {6.903 5.821}} -design [ed] -lpp {M2 drawing} -net VSS

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {3.833 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {3.907 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {3.981 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.055 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.129 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.203 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.277 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.351 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.425 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.499 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.573 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.647 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.721 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.795 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.869 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {4.943 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.017 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.091 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.165 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.239 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.313 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.387 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.461 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.535 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.609 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.683 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.757 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.831 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.905 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {5.979 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.053 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.127 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.201 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.275 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.349 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.423 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.497 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.571 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.645 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.719 5.804} -context [db::getNext [de::getContexts -window 2]]

ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA12} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
de::addPoint {6.793 5.804} -context [db::getNext [de::getContexts -window 2]]
