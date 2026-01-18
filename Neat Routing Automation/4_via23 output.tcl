# MODULE 4: VIA 23 GENERATION
# X_START: 3.823 microns, X_STEP: 0.373 microns
ile::createVia
gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
gi::setField {viaDefName} -value {VIA23} -in [gi::getToolbars {deCommandOptions} -from [gi::getWindows 2]]
ile::createVia
de::addPoint {3.823 6.957} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {3.823 7.525} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {3.823 7.635} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {3.823 8.203} -context [db::getNext [de::getContexts -window 2]]
le::createRectangle {{3.783 6.957} {3.863 8.203}} -design [ed] -lpp {M3 drawing} -net V2
ile::createVia
de::addPoint {4.196 8.784} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {4.196 9.785} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {4.196 9.984} -context [db::getNext [de::getContexts -window 2]]
le::createRectangle {{4.156 8.784} {4.236 9.984}} -design [ed] -lpp {M3 drawing} -net VDD
ile::createVia
de::addPoint {4.569 5.804} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {4.569 6.377} -context [db::getNext [de::getContexts -window 2]]
le::createRectangle {{4.529 5.804} {4.609 6.377}} -design [ed] -lpp {M3 drawing} -net VSS
ile::createVia
de::addPoint {4.942 5.931} -context [db::getNext [de::getContexts -window 2]]
le::createRectangle {{4.902 5.931} {4.982 6.431}} -design [ed] -lpp {M3 drawing} -net Vb
ile::createVia
de::addPoint {5.316 6.861} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {5.316 7.429} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {5.316 7.731} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {5.316 8.299} -context [db::getNext [de::getContexts -window 2]]
le::createRectangle {{5.276 6.861} {5.356 8.299}} -design [ed] -lpp {M3 drawing} -net Vin
ile::createVia
de::addPoint {5.689 6.702} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {5.689 7.270} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {5.689 7.893} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {5.689 8.461} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {5.689 8.974} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {5.689 9.597} -context [db::getNext [de::getContexts -window 2]]
le::createRectangle {{5.649 6.702} {5.729 9.597}} -design [ed] -lpp {M3 drawing} -net Vout
ile::createVia
de::addPoint {6.062 6.189} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {6.062 6.512} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {6.062 7.080} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {6.062 8.081} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {6.062 8.649} -context [db::getNext [de::getContexts -window 2]]
le::createRectangle {{6.022 6.189} {6.102 8.649}} -design [ed] -lpp {M3 drawing} -net net48
ile::createVia
de::addPoint {6.435 6.607} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {6.435 7.175} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {6.435 7.987} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {6.435 8.555} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {6.435 8.879} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {6.435 9.229} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {6.435 9.339} -context [db::getNext [de::getContexts -window 2]]
ile::createVia
de::addPoint {6.435 9.691} -context [db::getNext [de::getContexts -window 2]]
le::createRectangle {{6.395 6.607} {6.475 9.691}} -design [ed] -lpp {M3 drawing} -net net7