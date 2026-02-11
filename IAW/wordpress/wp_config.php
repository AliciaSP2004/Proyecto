<?php
/**
 * The base configuration for WordPress
 *
 * The wp-config.php creation script uses this file during the installation.
 * You don't have to use the website, you can copy this file to "wp-config.php"
 * and fill in the values.
 *
 * This file contains the following configurations:
 *
 * * Database settings
 * * Secret keys
 * * Database table prefix
 * * ABSPATH
 *
 * @link https://developer.wordpress.org/advanced-administration/wordpress/wp-config/
 *
 * @package WordPress
 */

// ** Database settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define( 'DB_NAME', 'Prunn' );

/** Database username */
define( 'DB_USER', 'root' );

/** Database password */
define( 'DB_PASSWORD', 'usuario@1' );

/** Database hostname */
define( 'DB_HOST', '10.0.2.110' );

/** Database charset to use in creating database tables. */
define( 'DB_CHARSET', 'utf8mb4' );

/** The database collate type. Don't change this if in doubt. */
define( 'DB_COLLATE', '' );

/**#@+
 * Authentication unique keys and salts.
 *
 * Change these to different unique phrases! You can generate these using
 * the {@link https://api.wordpress.org/secret-key/1.1/salt/ WordPress.org secret-key service}.
 *
 * You can change these at any point in time to invalidate all existing cookies.
 * This will force all users to have to log in again.
 *
 * @since 2.6.0
 */
define( 'AUTH_KEY',         ' KICDwS*blwfT@db@m ]qf<ewx|rUu0g9T]&>ztT3t$f;CL2,Sd];.YW,|pHWBgx' );
define( 'SECURE_AUTH_KEY',  'sTZvhUIfkfR&Y= oFA`:fJz~Z8PkcwpAU=T9P!`[t,y1q?# rZ.G16yB3Wni*u|l' );
define( 'LOGGED_IN_KEY',    'j@oy[N9`%3oFO@4+HfeZ9a[#?Y[eq7_R+;r`(I0EDB~wJxO%STtf&qp6v85E{:gU' );
define( 'NONCE_KEY',        'e=Ro$=OQM[D-M[DB!&xrFjELrzz%,=@7|aTY8Z}r/-so.UdUVF(Ou2<&$@OWOj86' );
define( 'AUTH_SALT',        'O6vFGA`jZ>,$c%(()OA.=oXMX4a2ZPmLz.Qr@3T{#[z9in5w_}yz/(T&H%P#_Ut=' );
define( 'SECURE_AUTH_SALT', '16A y|JL,A!hL8n.xDr2]i_,dL0{H2bmAM9akTwRl]lNdm BYv/Mg??;^OVhO*$K' );
define( 'LOGGED_IN_SALT',   'HrAL=pD#wg)jXj8z,aDx `Ca{ZsL2WWK|qF0HPpc1zC=0y$ 5qmnk:xF6#|w(fFw' );
define( 'NONCE_SALT',       'Gtxn$y+d|Y~p2uP13u[PB)USi7#`)(Xfyi<$h@q%7tR9Tpoi$-])a)c~1yO?bVb9' );

/**#@-*/

/**
 * WordPress database table prefix.
 *
 * You can have multiple installations in one database if you give each
 * a unique prefix. Only numbers, letters, and underscores please!
 *
 * At the installation time, database tables are created with the specified prefix.
 * Changing this value after WordPress is installed will make your site think
 * it has not been installed.
 *
 * @link https://developer.wordpress.org/advanced-administration/wordpress/wp-config/#table-prefix
 */
$table_prefix = 'wp_valles';

/**
 * For developers: WordPress debugging mode.
 *
 * Change this to true to enable the display of notices during development.
 * It is strongly recommended that plugin and theme developers use WP_DEBUG
 * in their development environments.
 *
 * For information on other constants that can be used for debugging,
 * visit the documentation.
 *
 * @link https://developer.wordpress.org/advanced-administration/debug/debug-wordpress/
 */
define( 'WP_DEBUG', false );

/* Add any custom values between this line and the "stop editing" line. */



/* That's all, stop editing! Happy publishing. */

/** Absolute path to the WordPress directory. */
if ( ! defined( 'ABSPATH' ) ) {
        define( 'ABSPATH', __DIR__ . '/' );
}

/** Sets up WordPress vars and included files. */
require_once ABSPATH . 'wp-settings.php';
