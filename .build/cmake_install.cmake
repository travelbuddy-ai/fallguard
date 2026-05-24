# Install script for directory: /Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "0")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "TRUE")
endif()

# Set path to fallback-tool for dependency-resolution.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/platform/tools/arm-gnu-toolchain-13.3.rel1-darwin-arm64-arm-none-eabi/bin/arm-none-eabi-objdump")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/tools/kconfiglib/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/audio_player/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/common/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/libcjson/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/libhttp/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/liblvgl/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/liblwip/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/libmqtt/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/libtls/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/libu8g2/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/micropython/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/peripherals/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tal_bluetooth/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tal_cellular/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tal_cli/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tal_driver/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tal_image/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tal_kv/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tal_network/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tal_security/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tal_system/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tal_wifi/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tal_wired/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tuya_ai_service/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tuya_cloud_service/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/src/tuya_p2p/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/boards/T5AI/TUYA_T5AI_BOARD/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/apps/tuya.ai/ai_components/cmake_install.cmake")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
if(CMAKE_INSTALL_LOCAL_ONLY)
  file(WRITE "/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/install_local_manifest.txt"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
endif()
if(CMAKE_INSTALL_COMPONENT)
  if(CMAKE_INSTALL_COMPONENT MATCHES "^[a-zA-Z0-9_.+-]+$")
    set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
  else()
    string(MD5 CMAKE_INST_COMP_HASH "${CMAKE_INSTALL_COMPONENT}")
    set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INST_COMP_HASH}.txt")
    unset(CMAKE_INST_COMP_HASH)
  endif()
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  file(WRITE "/Users/jonathanpaezlindsey/Desktop/git_repo/TuyaOpen/apps/tuya.ai/travelbuddy/.build/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
endif()
