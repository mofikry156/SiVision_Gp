db::destroy [db::getShapes -lpp {M3 drawing} -of $design]
db::destroy [db::getShapes -lpp {M2 drawing} -of $design]
db::destroy [db::getVias -of $design]
db::destroy [db::getShapes -lpp {VIA2 drawing} -of $design]
