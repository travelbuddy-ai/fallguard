file(GLOB_RECURSE FALLGUARD_UI_SRCS "*.c")
target_sources(${COMPONENT_NAME} PRIVATE ${FALLGUARD_UI_SRCS})
target_include_directories(${COMPONENT_NAME} PUBLIC .)
